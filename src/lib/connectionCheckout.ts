type CheckoutOrder={order_id?:string;amount?:number;currency?:string;key_id?:string;already_paid?:boolean;local_simulation?:boolean}
type CheckoutInstance={open:()=>void;on?:(name:string,callback:()=>void)=>void}
declare global{interface Window{Razorpay?:new(options:Record<string,unknown>)=>CheckoutInstance}}
let sdk:Promise<void>|null=null
export async function openConnectionCheckout(order:CheckoutOrder,confirmed:()=>void,cancelled:()=>void){
 if(order.already_paid){confirmed();return}
 if(order.local_simulation){cancelled();return}
 if(!order.order_id||!order.key_id||!order.amount||!order.currency)throw new Error('Checkout is unavailable. No contact has been unlocked.')
 if(!window.Razorpay){sdk??=new Promise<void>((resolve,reject)=>{const script=document.createElement('script');script.src='https://checkout.razorpay.com/v1/checkout.js';script.onload=()=>resolve();script.onerror=()=>{sdk=null;reject(new Error('Checkout could not load. Your selection remains available.'))};document.head.appendChild(script)});await sdk}
 if(!window.Razorpay)throw new Error('Checkout could not start.')
 const checkout=new window.Razorpay({key:order.key_id,order_id:order.order_id,amount:order.amount,currency:order.currency,name:'TransivoX',description:'One-time platform connection fee — freight is separate',handler:confirmed,modal:{ondismiss:cancelled}})
 checkout.on?.('payment.failed',cancelled);checkout.open()
}
