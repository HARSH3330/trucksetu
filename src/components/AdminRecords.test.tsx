import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AdminRecords from './AdminRecords'

it('shows loading without invented admin records',()=>{
  const html=renderToStaticMarkup(<AdminRecords/>);
  expect(html).toContain('Loading operational records')
  expect(html).not.toContain('Harsh')
})
