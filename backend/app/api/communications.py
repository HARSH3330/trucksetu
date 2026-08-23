from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain import ensure_chat_allowed
from app.models import Booking, BookingAllocation, Conversation, ConversationParticipant, Message, Notification, NotificationPreference
from app.schemas import ConversationCreate, MessageCreate, NotificationPreferenceUpdate

router=APIRouter(prefix="/api/v1",tags=["communications"])


async def _booking_participants(db:AsyncSession,booking:Booking)->dict[uuid.UUID,str]:
    result={booking.customer_id:"customer"}
    for provider_id in await db.scalars(select(BookingAllocation.provider_id).where(BookingAllocation.booking_id==booking.id)):result[provider_id]="provider"
    return result


@router.get("/notifications")
async def list_notifications(user_id:uuid.UUID,unread_only:bool=False,db:AsyncSession=Depends(get_db))->dict[str,object]:
    query=select(Notification).where(Notification.user_id==user_id)
    if unread_only:query=query.where(Notification.read_at.is_(None))
    items=list(await db.scalars(query.order_by(Notification.created_at.desc()).limit(100)))
    unread=await db.scalar(select(func.count(Notification.id)).where(Notification.user_id==user_id,Notification.read_at.is_(None)))
    return {"unread_count":int(unread or 0),"items":[{"id":str(x.id),"event_type":x.event_type,"title":x.title,"body":x.body,"read":x.read_at is not None,"created_at":x.created_at.isoformat()} for x in items]}


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id:uuid.UUID,user_id:uuid.UUID,db:AsyncSession=Depends(get_db))->dict[str,bool]:
    item=await db.scalar(select(Notification).where(Notification.id==notification_id,Notification.user_id==user_id).with_for_update())
    if item is None:raise HTTPException(status_code=404,detail="Notification not found")
    item.read_at=datetime.now(UTC);return {"read":True}


@router.put("/users/{user_id}/notification-preferences")
async def update_preferences(user_id:uuid.UUID,payload:NotificationPreferenceUpdate,db:AsyncSession=Depends(get_db))->dict[str,object]:
    item=await db.get(NotificationPreference,user_id)
    if item is None:item=NotificationPreference(user_id=user_id);db.add(item)
    for key,value in payload.model_dump().items():setattr(item,key,value)
    return payload.model_dump()


@router.post("/conversations",status_code=status.HTTP_201_CREATED)
async def create_conversation(payload:ConversationCreate,db:AsyncSession=Depends(get_db))->dict[str,str]:
    existing=await db.scalar(select(Conversation).where(Conversation.booking_id==payload.booking_id))
    if existing:return {"id":str(existing.id),"status":existing.status}
    booking=await db.get(Booking,payload.booking_id)
    if booking is None:raise HTTPException(status_code=404,detail="Booking not found")
    participants=await _booking_participants(db,booking)
    try:ensure_chat_allowed(booking.status,str(payload.requester_id),{str(x) for x in participants})
    except PermissionError as exc:raise HTTPException(status_code=403,detail=str(exc)) from exc
    conversation=Conversation(booking_id=booking.id)
    db.add(conversation);await db.flush()
    db.add_all([ConversationParticipant(conversation_id=conversation.id,user_id=user_id,role=role) for user_id,role in participants.items()])
    return {"id":str(conversation.id),"status":conversation.status}


@router.get("/conversations/{conversation_id}/messages")
async def list_messages(conversation_id:uuid.UUID,user_id:uuid.UUID,db:AsyncSession=Depends(get_db))->list[dict[str,str]]:
    participant=await db.scalar(select(ConversationParticipant).where(ConversationParticipant.conversation_id==conversation_id,ConversationParticipant.user_id==user_id))
    if participant is None:raise HTTPException(status_code=403,detail="You are not part of this conversation")
    participant.last_read_at=datetime.now(UTC)
    items=list(await db.scalars(select(Message).where(Message.conversation_id==conversation_id,Message.deleted_at.is_(None)).order_by(Message.created_at).limit(500)))
    return [{"id":str(x.id),"sender_id":str(x.sender_id),"body":x.body,"created_at":x.created_at.isoformat()} for x in items]


@router.post("/conversations/{conversation_id}/messages",status_code=status.HTTP_201_CREATED)
async def send_message(conversation_id:uuid.UUID,payload:MessageCreate,db:AsyncSession=Depends(get_db))->dict[str,str]:
    conversation=await db.get(Conversation,conversation_id)
    if conversation is None or conversation.status!="active":raise HTTPException(status_code=409,detail="Conversation is unavailable")
    booking=await db.get(Booking,conversation.booking_id);participants=await _booking_participants(db,booking) if booking else {}
    try:ensure_chat_allowed(booking.status if booking else "cancelled",str(payload.sender_id),{str(x) for x in participants})
    except PermissionError as exc:raise HTTPException(status_code=403,detail=str(exc)) from exc
    item=Message(conversation_id=conversation.id,**payload.model_dump());db.add(item);await db.flush()
    for user_id in participants:
        if user_id!=payload.sender_id:db.add(Notification(user_id=user_id,event_type="chat.message",title="New booking message",body=payload.body[:180],entity_type="conversation",entity_id=conversation.id,data={"booking_id":str(conversation.booking_id)}))
    return {"id":str(item.id),"created_at":datetime.now(UTC).isoformat()}
