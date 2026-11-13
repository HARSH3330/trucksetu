import ConnectionFeeReview from './ConnectionFeeReview'
import AdminRecords from './AdminRecords'
import SharedMatchReview from './SharedMatchReview'
import {useEffect, useState} from 'react'
import {AlertTriangle, BadgeCheck, CheckCircle2, FileText, IndianRupee, LockKeyhole, PackageCheck, Route, ShieldCheck, Truck, UsersRound} from 'lucide-react'
import {ApiError, apiFetch} from '../lib/api'
import './LiveAdmin.css'

type Health={verified_providers:number;approved_vehicles:number;open_requests:number;active_quotes:number;active_bookings:number;open_disputes:number;pending_kyc:number;gmv:string;total_bookings:number;completed_bookings:number;completion_rate:number
  open_requirements:number;open_bids:number;requirements_without_bids:number;total_customers:number;total_truck_owners:number;verified_truck_owners:number;total_trucks:number;total_drivers:number;total_trips:number;active_trips:number;completed_trips:number;paid_connections:number;pending_customer_kyc:number;unverified_contacts:number}
type Funnel={period_days:number;funnel:{stage:string;count:number}[]}
const plural=(count:number,word:string)=>`${count} ${word}${count===1?'':'s'}`

/** What needs a decision first, then the numbers an operator checks every day. */
export function AdminOverview({health,openKyc,openVehicles,openDisputes}:{health:Health;openKyc:()=>void;openVehicles:()=>void;openDisputes:()=>void}){
  const waiting=health.pending_kyc+health.pending_customer_kyc
  const stats:[typeof UsersRound,string,string,string][]=[
    [FileText,'Open requirements',String(health.open_requirements),`${health.requirements_without_bids} without bids`],
    [PackageCheck,'Open bids',String(health.open_bids),'Active bids on open requirements'],
    [UsersRound,'Customers',String(health.total_customers),'Active customer accounts'],
    [UsersRound,'Truck owners',String(health.total_truck_owners),`Verified truck owners: ${health.verified_truck_owners}`],
    [Truck,'Trucks',String(health.total_trucks),`Approved trucks: ${health.approved_vehicles}`],
    [UsersRound,'Drivers',String(health.total_drivers),'Linked to truck owners'],
    [Route,'Trips',String(health.total_trips),`${health.active_trips} in progress · ${health.completed_trips} completed`],
    [BadgeCheck,'Active bookings',String(health.active_bookings),`${health.completion_rate}% of ${health.total_bookings} completed`],
    [LockKeyhole,'Paid connections',String(health.paid_connections),'Connection fees captured'],
    [IndianRupee,'Booking value',`₹${Number(health.gmv).toLocaleString('en-IN')}`,'Bookings not cancelled'],
  ]
  return <>
    <section className="admin-attention" aria-labelledby="attention-title">
      <h2 id="attention-title">Needs your attention</h2>
      <div className="attention-grid">
        {waiting>0&&<div className="attention-card warn"><ShieldCheck/><div><b>{plural(waiting,'verification')} waiting</b><small>Customers or truck owners sent documents for review.</small></div><button onClick={openKyc}>Review verifications</button></div>}
        {health.open_disputes>0&&<div className="attention-card bad"><AlertTriangle/><div><b>{plural(health.open_disputes,'open dispute')}</b><small>A customer or truck owner reported a problem.</small></div><button onClick={openDisputes}>Open disputes</button></div>}
        {!waiting&&!health.open_disputes&&<div className="attention-card ok"><CheckCircle2/><div><b>All clear</b><small>No verifications or disputes are waiting.</small></div></div>}
        {health.unverified_contacts>0&&<div className="attention-card"><UsersRound/><div><b>{plural(health.unverified_contacts,'account')} without a verified email or phone</b><small>They cannot publish or bid yet. Check them under Users below.</small></div></div>}
        <div className="attention-card"><Truck/><div><b>Truck approvals</b><small>New trucks need their 5 documents accepted before they can take loads.</small></div><button className="secondary" onClick={openVehicles}>Open truck queue</button></div>
      </div>
    </section>
    <div className="stat-grid admin-stats">{stats.map(([Icon,label,value,note])=><div className="stat" key={label}><span><Icon/></span><small>{label}</small><strong>{value}</strong><em>{note}</em></div>)}</div>
  </>
}

export default function LiveAdmin({openKyc,openVehicles,openOperations,superadmin=false}:{openKyc:()=>void;openVehicles:()=>void;openOperations:(view:'bookings'|'trips'|'payments'|'invoices'|'trust')=>void;superadmin?:boolean}){
  const [health,setHealth]=useState<Health|null>(null)
  const [funnel,setFunnel]=useState<Funnel|null>(null)
  const [state,setState]=useState<'loading'|'ready'|'forbidden'|'error'>('loading')
  function load(){setState('loading');Promise.all([apiFetch<Health>('/admin/marketplace-health'),apiFetch<Funnel>('/admin/analytics/funnel')]).then(([a,b])=>{setHealth(a);setFunnel(b);setState('ready')}).catch(error=>setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error'))}
  useEffect(load,[])
  if(state==='loading')return <main className="page"><div className="empty-state">Loading marketplace operations…</div></main>
  if(state==='forbidden')return <main className="page"><div className="empty-state"><b>Administrator access required</b><p>This area is not available to customer or provider accounts.</p></div></main>
  if(state==='error'||!health||!funnel)return <main className="page"><div className="empty-state"><b>Operations unavailable</b><button onClick={load}>Retry</button></div></main>
  const max=Math.max(1,...funnel.funnel.map(item=>item.count))
  return <main className="page admin-page">
    <div className="page-title"><span className="kicker">OPERATIONS</span><h1>Marketplace control centre</h1><p>Check what needs a decision, then manage people, requirements and bookings.</p></div>
    <nav className="fleet-tabs admin-links" aria-label="Admin areas"><button onClick={openKyc}>Verification</button><button onClick={openVehicles}>Truck approvals</button>{([['bookings','Bookings'],['trips','Trips'],['payments','Payments'],['invoices','Invoices'],['trust','Disputes & safety']] as const).map(([view,label])=><button key={view} onClick={()=>openOperations(view)}>{label}</button>)}</nav>
    <AdminOverview health={health} openKyc={openKyc} openVehicles={openVehicles} openDisputes={()=>openOperations('trust')}/>
    <AdminRecords superadmin={superadmin}/>
    <ConnectionFeeReview/>
    <SharedMatchReview/>
    <details className="panel admin-funnel"><summary>{funnel.period_days}-day visitor funnel</summary><div className="funnel-chart">{funnel.funnel.map(item=><div key={item.stage}><span><b>{item.stage.replaceAll('_',' ')}</b><small>{item.count}</small></span><i><em style={{width:`${item.count/max*100}%`}}/></i></div>)}</div></details>
  </main>
}
