import type {PurchasedContact} from '../lib/demand-types'

/** The contact a customer paid for, saying which channel was actually verified. */
export default function PurchasedContactCard({contact}:{contact:PurchasedContact}){
  return <div className="purchased-contact">
    <h4>Your {contact.contact_kind} contact</h4>
    <p>{contact.contact_name}</p>
    <a href={`tel:${contact.phone}`}>{contact.phone}</a>
    <p className="contact-check">{contact.phone_verified?'Phone verified by SMS':'Phone not verified by SMS — the number is as the provider entered it'}</p>
    {contact.email&&<><a href={`mailto:${contact.email}`}>{contact.email}</a><p className="contact-check">Email verified</p></>}
    {contact.driver_phone&&<><h4>Assigned driver</h4><p>{contact.driver_name}</p><a href={`tel:${contact.driver_phone}`}>{contact.driver_phone}</a><p className="contact-check">{contact.driver_phone_verified?'Phone verified by SMS':'Phone not verified by SMS'}</p></>}
    <p>{contact.notice}</p>
  </div>
}
