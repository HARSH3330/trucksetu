export type DemandCargo={category:string;description:string;weight_tonnes:string;length_m:string;width_m:string;height_m:string;packages:number|null;packaging_type:string|null;dimensions_are_per_package:boolean;loading_assistance:boolean;unloading_assistance:boolean;fragile:boolean;volume_m3:string}
export type Demand={id:string;public_id:string;revision:number;status:string;pickup_city:string;destination_city:string;pickup_address?:string;destination_address?:string;pickup_location?:{lat:number;lng:number}|null;destination_location?:{lat:number;lng:number}|null;pickup_date:string;earliest_pickup_at:string;latest_pickup_at:string;delivery_deadline_at:string;flexible_schedule:boolean;budget_amount:string|null;special_instructions?:string|null;cargo:DemandCargo}
export type DemandBid={id:string;request_id:string;version:number;request_revision:number;status:string;provider_name:string;provider_verified:boolean;amount:string;currency:string;pickup_at:string;delivery_at:string;expires_at:string;inclusions:string;exclusions:string;notes:string|null;contact_kind:'provider'|'driver';vehicle:{body_type:string;payload_tonnes:string;volume_m3:string}}
export type Fee={version:string|null;amount:string;total:string;currency:string;basis:string;tax_treatment:string;tax_amount:string|null;tax_rate?:string;tax_confirmed?:boolean;connection_fee_waived?:boolean;waiver_label?:string;waiver_tax_treatment?:string;test_only?:boolean;terms?:string;cancellation_terms?:string;provider_failure_terms?:string;replacement_terms?:string}
export type MarketplaceConfig={mode:string;enabled:boolean;legacy_provider_operations:boolean;provider_first_publication_available:boolean;publication_available:boolean;checkout_available:boolean;real_checkout_available:boolean;fee:Fee;driver_assignment:string|null}
export type Selection={id:string;vehicle_id:string;request_id:string;quote_id:string;booking_id:string;status:string;payment_status:string;expires_at:string;order_state:string;quote:DemandBid;fee:Fee;contact_state:string;contact_revealed_at?:string|null;credit_id?:string|null;contact_kind:'provider'|'driver';contact_label:string;assignment_state:string;freight_payment_separate:boolean;refund?:{id:string;status:string;amount:string;tax_amount:string|null;currency:string}|null}
export type PurchasedContact={state:'locked'|'eligible'|'unavailable'|'unlocked';contact_kind?:'provider'|'driver';contact_name?:string;phone?:string;driver_name?:string;driver_phone?:string;notice?:string}
export type Draft={id:string;version:number;payload:Record<string,string|boolean>;updated_at:string}
export const money=(amount:string,currency='INR')=>new Intl.NumberFormat('en-IN',{style:'currency',currency,maximumFractionDigits:2}).format(Number(amount))
export const dateTime=(value:string)=>new Date(value).toLocaleString('en-IN',{dateStyle:'medium',timeStyle:'short'})
export const stateLabel=(value:string)=>({published:'Open for bids',selection_pending:'Connection fee pending',allocated:'Booked',active:'Bid submitted',selected:'Selected — connection fee pending',accepted:'Selected — connection fee paid',paid:'Connection fee paid',review_required:'Operations review required',connection_fee_pending:'Connection fee pending'}[value]||value.replaceAll('_',' '))

export function connectionRefundMessage(status:string,amount:string,currency='INR'){
 const full=money(amount,currency)
 if(status==='requested')return `Full refund requested: ${full} including tax. Processing is pending; contact access is blocked.`
 if(status==='pending')return `Refund processing is pending: ${full} including tax. Contact access remains blocked.`
 if(status==='unknown')return `Refund execution is not confirmed. The ${full} refund obligation remains open and contact is blocked.`
 if(status==='failed'||status==='review_required')return `Refund needs operations review. The ${full} refund obligation remains open and contact is blocked.`
 if(status==='processed')return `Refund status recorded as processed: ${full}. Contact access remains blocked.`
 if(status==='no_captured_payment')return 'Connection cancelled. No captured payment is recorded and no refund has been executed.'
 return 'Connection cancelled. Contact was revealed; ordinary cancellation has no refund.'
}
