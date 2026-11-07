import {useEffect,useState} from 'react'
import {ArrowRight as ArrowRightIcon,Check,FileText,MapPin,Phone,Truck,Users,BadgeCheck} from 'lucide-react'
import {publicFetch,type CurrentUser} from '../lib/api'
import {money,type MarketplaceConfig} from '../lib/demand-types'
import type {View} from '../lib/routes'
import {checkoutSentence,taxSentence} from '../lib/fee-copy'
import VerificationCard from './VerificationCard'
import './DemandMarketplace.css'

/** Fee facts come from the server's live settings, never from fixed text. */
export function HomeFeeNotice({config}:{config:MarketplaceConfig|null}){
 return <p>{taxSentence(config)} Before contact reveal, cancellation qualifies for a full refund including tax. After reveal, ordinary cancellation has no refund. Administrator-confirmed provider failure can issue one single-use platform-fee credit. Tax on a waived fee, credit expiry, transferability and invalid-contact rules remain unresolved. {checkoutSentence(config)}</p>
}

const HOW_STEPS=[
 [FileText,'Post your load','Route, date and what you are moving.'],
 [Users,'Get bids','Verified truck owners send their prices.'],
 [BadgeCheck,'Pick the best','Compare price, timing and truck size.'],
 [Phone,'Call and go','Pay the connection fee to get their number, then settle freight with them.'],
] as const

export default function CustomerHome({navigate,user=null,sessionLoading=false}:{navigate:(view:View)=>void;user?:CurrentUser|null;sessionLoading?:boolean}){
 const [config,setConfig]=useState<MarketplaceConfig|null>(null)
 useEffect(()=>{publicFetch<MarketplaceConfig>('/marketplace').then(setConfig).catch(()=>setConfig(null))},[])
 return <main><section className="customer-hero"><div><h1>Post a load.<br/>Compare bids.</h1><p>Tell us what needs moving. Verified transport providers send their quotes. Choose the provider that suits your goods and timing.</p><button className="customer-primary" onClick={()=>navigate('ship')}>Post a transport requirement<ArrowRightIcon/></button><br/><ul className="hero-facts"><li><Check/>Free to post a requirement</li><li><Check/>Bids from verified truck owners</li><li><Check/>Pay only to get the number</li></ul><a href="#loads" className="customer-secondary">For fleet owners — browse customer demands</a></div><div className="customer-how" aria-labelledby="how-title"><div className="route-visual" aria-hidden="true"><span className="route-pin route-pin-start"><MapPin/></span><span className="route-road"><span className="route-truck"><Truck/></span></span><span className="route-pin route-pin-end"><MapPin/></span></div><h2 id="how-title">How it works</h2><ol className="how-steps">{HOW_STEPS.map(([Icon,title,text],index)=><li key={title} style={{animationDelay:`${index*90}ms`}}><span className="how-icon" aria-hidden="true"><Icon/></span><div><b>{title}</b><small>{text}</small></div></li>)}</ol></div></section><section className="customer-fee"><h2>Connection fee, separate from freight</h2><p>{config?.fee?`${money(config.fee.amount,config.fee.currency)} per booking, paid once for verified contact access.`:'The server-confirmed connection fee is shown before checkout. It is currently unavailable.'} This is not the transport fare, a freight deposit or an advance toward transportation.</p><p>Checkout says whether you are buying provider or assigned-driver contact. That verified number must be available before payment. Reopen an already purchased contact without paying again; a verified driver added later to the same booking is included.</p><HomeFeeNotice config={config}/></section><section className="page demand-page"><VerificationCard user={user} sessionLoading={sessionLoading} onOpen={()=>navigate('kyc')} onSignIn={()=>navigate('kyc')}/><h2>Useful details make useful bids</h2><p>Enter pickup and delivery areas, a time window, what you are moving, total weight and load dimensions. Save a draft if you need to check a measurement. Precise addresses stay out of public demand listings.</p><details><summary>Do I need to know which truck to choose?</summary><p>No. Describe the goods and handling needs. Providers bid using their suitable verified vehicles.</p></details><details><summary>Does paying the connection fee pay for transport?</summary><p>No. The connection fee buys access to the promised verified contact for that booking. You arrange the trip and settle the provider’s transport charge directly.</p></details><details><summary>What about shared capacity?</summary><p>The existing shared-capacity implementation is retained. Single-winner bidding does not remove its capacity protections or decide future demand aggregation.</p><a href="#capacity">Open shared-capacity tools</a></details></section></main>
}
