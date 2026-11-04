import {useEffect, useState} from 'react'
import {ArrowRight, Bell, Check, Clock3, MessageCircle, ShieldCheck} from 'lucide-react'
import {ApiError, apiFetch, type ChatMessage, type Conversation, type CurrentUser, type NotificationFeed, type NotificationPreferences} from '../lib/api'
import './LiveCommunications.css'

type Booking = {id:string;public_id:string;status:string;pickup:string;destination:string}
const defaults:NotificationPreferences={in_app:true,email:true,sms:true,whatsapp:false,quiet_hours_start:null,quiet_hours_end:null}

export default function LiveCommunications(){
  const [tab,setTab]=useState<'messages'|'notifications'|'preferences'>('messages')
  const [me,setMe]=useState<CurrentUser|null>(null)
  const [conversations,setConversations]=useState<Conversation[]>([])
  const [bookings,setBookings]=useState<Booking[]>([])
  const [active,setActive]=useState('')
  const [messages,setMessages]=useState<ChatMessage[]>([])
  const [notifications,setNotifications]=useState<NotificationFeed>({unread_count:0,items:[]})
  const [preferences,setPreferences]=useState(defaults)
  const [draft,setDraft]=useState('')
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [notice,setNotice]=useState('')

  function load(){
    setState('loading')
    Promise.all([apiFetch<CurrentUser>('/auth/me'),apiFetch<Conversation[]>('/conversations'),apiFetch<Booking[]>('/bookings'),apiFetch<NotificationFeed>('/notifications'),apiFetch<NotificationPreferences>('/users/me/notification-preferences')])
      .then(([user,chats,userBookings,feed,prefs])=>{setMe(user);setConversations(chats);setBookings(userBookings);setNotifications(feed);setPreferences(prefs);setActive(chats[0]?.id||'');setState('ready')})
      .catch(error=>setState(error instanceof ApiError&&error.status===401?'signed-out':'error'))
  }
  useEffect(load,[])
  useEffect(()=>{if(active)apiFetch<ChatMessage[]>(`/conversations/${active}/messages`).then(setMessages).catch(error=>setNotice(error instanceof Error?error.message:'Messages unavailable'));else setMessages([])},[active])

  async function start(bookingId:string){
    try{const result=await apiFetch<{id:string}>('/conversations',{method:'POST',body:JSON.stringify({booking_id:bookingId})});const chats=await apiFetch<Conversation[]>('/conversations');setConversations(chats);setActive(result.id);setNotice('')}
    catch(error){setNotice(error instanceof Error?error.message:'Conversation could not be opened')}
  }
  async function send(){
    if(!active||!draft.trim())return
    try{await apiFetch(`/conversations/${active}/messages`,{method:'POST',body:JSON.stringify({body:draft.trim(),attachment_keys:[]})});setDraft('');setMessages(await apiFetch<ChatMessage[]>(`/conversations/${active}/messages`))}
    catch(error){setNotice(error instanceof Error?error.message:'Message could not be sent')}
  }
  async function markRead(id:string){await apiFetch(`/notifications/${id}/read`,{method:'POST'});setNotifications(await apiFetch<NotificationFeed>('/notifications'))}
  async function savePreferences(){
    try{setPreferences(await apiFetch<NotificationPreferences>('/users/me/notification-preferences',{method:'PUT',body:JSON.stringify(preferences)}));setNotice('Preferences saved.')}
    catch(error){setNotice(error instanceof Error?error.message:'Preferences could not be saved')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading your communications…</div></main>
  if(state==='signed-out')return <main className="page"><div className="page-title"><h1>Messages & notifications</h1></div><div className="empty-state"><b>Sign in required</b><p>Your booking conversations and alerts are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Communications unavailable</b><p>Please try again.</p><button onClick={load}>Retry</button></div></main>
  return <main className="page"><div className="page-title"><span className="kicker">PRIVATE & BOOKING-LINKED</span><h1>Messages & notifications</h1><p>Communicate without exposing contact details before a confirmed booking.</p></div><div className="communication-tabs"><button className={tab==='messages'?'active':''} onClick={()=>setTab('messages')}><MessageCircle/> Messages</button><button className={tab==='notifications'?'active':''} onClick={()=>setTab('notifications')}><Bell/> Notifications {notifications.unread_count>0&&<b>{notifications.unread_count}</b>}</button><button className={tab==='preferences'?'active':''} onClick={()=>setTab('preferences')}>Preferences</button></div>{notice&&<div className="privacy-banner">{notice}</div>}
    {tab==='messages'&&<div className="live-messenger"><aside>{conversations.map(chat=><button className={active===chat.id?'active':''} onClick={()=>setActive(chat.id)} key={chat.id}><b>{chat.booking_public_id}</b><small>{chat.role} · {chat.status}</small></button>)}{bookings.filter(booking=>!conversations.some(chat=>chat.booking_id===booking.id)).map(booking=><button onClick={()=>start(booking.id)} key={booking.id}><b>{booking.public_id}</b><small>Start booking conversation</small></button>)}{!bookings.length&&!conversations.length&&<p>No eligible bookings yet.</p>}</aside><section><div className="privacy-banner"><ShieldCheck/> Messages are retained with the booking for safety.</div><div className="message-list">{messages.map(message=><div className={`bubble ${message.sender_id===me?.id?'mine':''}`} key={message.id}><p>{message.body}</p><small>{new Date(message.created_at).toLocaleString('en-IN')}</small></div>)}{active&&!messages.length&&<div className="empty-state">No messages yet.</div>}</div>{active&&<div className="message-compose"><input value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} maxLength={5000} placeholder="Write a booking message"/><button onClick={send} disabled={!draft.trim()}><ArrowRight/></button></div>}</section></div>}
    {tab==='notifications'&&<div className="notification-list">{notifications.items.map(item=><article className={!item.read?'unread':''} key={item.id}><span><Bell/></span><div><b>{item.title}</b><p>{item.body}</p><small>{new Date(item.created_at).toLocaleString('en-IN')}</small></div>{!item.read&&<button onClick={()=>markRead(item.id)}><Check/> Mark read</button>}</article>)}{!notifications.items.length&&<div className="empty-state">No notifications yet.</div>}</div>}
    {tab==='preferences'&&<div className="preference-panel"><div><h3>Delivery channels</h3><p>In-app notifications work now. External channels start after their providers are configured.</p></div>{([['in_app','In-app notifications'],['email','Email'],['sms','SMS'],['whatsapp','WhatsApp']] as const).map(([key,label])=><label className="preference-row" key={key}><span><b>{label}</b><small>{key==='in_app'?'Booking and account alerts inside TransivoX':'Saved now; delivery requires provider configuration'}</small></span><input type="checkbox" checked={preferences[key]} onChange={e=>setPreferences({...preferences,[key]:e.target.checked})}/></label>)}<div className="quiet-hours"><Clock3/><span><b>Quiet hours</b><small>Optional local time for non-critical external notifications</small></span><input type="time" value={preferences.quiet_hours_start||''} onChange={e=>setPreferences({...preferences,quiet_hours_start:e.target.value||null})}/><input type="time" value={preferences.quiet_hours_end||''} onChange={e=>setPreferences({...preferences,quiet_hours_end:e.target.value||null})}/></div><button className="save-preferences" onClick={savePreferences}>Save preferences</button></div>}
  </main>
}
