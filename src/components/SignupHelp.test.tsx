import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import {PasswordChecklist,ROLE_CHOICES,passwordChecks} from './SignupHelp'

describe('sign-up help',()=>{
  it('explains every account type in plain words',()=>{
    expect(ROLE_CHOICES.map(choice=>choice.value)).toEqual(['customer','provider','fleet_owner','driver'])
    for(const choice of ROLE_CHOICES)expect(choice.help.length).toBeGreaterThan(20)
  })
  it('checks each password rule the server enforces',()=>{
    expect(passwordChecks('short')).toEqual([{label:'At least 10 characters',met:false},{label:'An uppercase letter',met:false},{label:'A lowercase letter',met:true},{label:'A number',met:false}])
    expect(passwordChecks('Fictional123').every(check=>check.met)).toBe(true)
  })
  it('announces which rules are met',()=>{
    const html=renderToStaticMarkup(<PasswordChecklist password="FictionalX"/>)
    expect(html).toContain('aria-live="polite"')
    const text=html.replace(/<[^>]+>/g,'')
    expect(text).toContain('Met: At least 10 characters')
    expect(text).toContain('Not yet: ○A number')
  })
})
