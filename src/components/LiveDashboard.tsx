import {useEffect, useState} from 'react'
import {ArrowRight, BadgeCheck, PackageCheck, Route, Star, Truck, WalletCards} from 'lucide-react'
import {ApiError, apiFetch} from '../lib/api'

type Summary={roles:string[];open_requests:number;active_quotes:number;active_bookings:number;active_trips:number;completed_bookings:number;total_booking_value:string;provider_rating:string|null;provider_kyc_status:string|null}
type Destination='capacity'|'bookings'|'quotes'|'kyc'|'fleet'
const money=(value:string)=>`₹${Number(value).toLocaleString('en-IN')}`

export default function LiveDashboard({navigate}:{navigate:(view:Destination)=>void}){
  const [data,setData]=useState<Summary|null>(null)
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  function load(){setState('loading');apiFetch<Summary>('/dashboard/summary').then(value=>{setData(value);setState('ready')}).catch(error=>setState(error instanceof ApiError&&error.status===401?'signed-out':'error'))}
  useEffect(load,[])
  if(state==='loading')return <main className="page"><div className="empty-state">Loading your dashboard…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Your operational dashboard is private.</p></div></main>
  if(state==='error'||!data)return <main className="page"><div className="empty-state"><b>Dashboard unavailable</b><button onClick={load}>Retry</button></div></main>
  const provider=data.roles.some(role=>['provider','fleet_owner'].includes(role))
  return <main className="page"><div className="page-title"><span className="kicker">LIVE ACCOUNT OVERVIEW</span><h1>{provider?'Provider dashboard':'Customer dashboard'}</h1><p>Calculated from your current TransivoX records.</p></div><div className="stat-grid"><div className="stat"><span><Route/></span><small>Active trips</small><strong>{data.active_trips}</strong><em>{data.active_bookings} active bookings</em></div><div className="stat"><span><PackageCheck/></span><small>{provider?'Quotes submitted':'Open requirements'}</small><strong>{provider?data.active_quotes:data.open_requests}</strong><em>{provider?'All submitted quotes':`${data.active_quotes} active quotes`}</em></div><div className="stat"><span><WalletCards/></span><small>Booking value</small><strong>{money(data.total_booking_value)}</strong><em>Excludes cancelled</em></div><div className="stat"><span><Star/></span><small>{provider?'Provider rating':'Completed bookings'}</small><strong>{provider?(data.provider_rating||'—'):data.completed_bookings}</strong><em>{provider?`KYC ${data.provider_kyc_status||'not started'}`:'Verified records'}</em></div></div><div className="dashboard-grid"><section className="panel"><div className="panel-head"><h3>Operational summary</h3><span className="badge">LIVE DATA</span></div><div className="activity"><span className="activity-icon"><Truck/></span><div><b>{data.active_bookings} bookings currently active</b><small>{data.active_trips} individual trips still in progress</small></div></div><div className="activity"><span className="activity-icon"><BadgeCheck/></span><div><b>{data.completed_bookings} completed bookings</b><small>Completion is recorded only by the trip workflow</small></div></div></section><section className="panel actions"><h3>Quick actions</h3><button onClick={()=>navigate('bookings')}><Truck/> View bookings <ArrowRight/></button><button onClick={()=>navigate('quotes')}><PackageCheck/> View quotations</button><button onClick={()=>navigate('capacity')}><Route/> Search shared capacity</button>{provider&&<><button onClick={()=>navigate('fleet')}><Truck/> Manage fleet & drivers</button><button onClick={()=>navigate('kyc')}><BadgeCheck/> Verification status</button></>}</section></div></main>
}
