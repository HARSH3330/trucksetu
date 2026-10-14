import {expect,test} from '@playwright/test'

test('public homepage does not advertise fake loads when API is unavailable',async({page})=>{
  await page.goto('/')
  await expect(page.locator('.load-card')).toHaveCount(0)
  await expect(page.getByText('Current loads are unavailable.',{exact:true})).toBeVisible()
  await expect(page.getByRole('button',{name:'Retry current loads',exact:true})).toBeVisible()
})

test('logo returns from capacity to home at mobile width',async({page})=>{
  await page.goto('/')
  await page.getByRole('link',{name:'Shared truck space',exact:true}).first().click()
  await expect(page.getByRole('heading',{name:'Trucks already going your way'})).toBeVisible()
  await page.setViewportSize({width:390,height:844})
  await page.getByRole('button',{name:'TransivoX',exact:true}).click()
  await expect(page.getByRole('heading',{name:'Transport quotes for your goods.'})).toBeVisible()
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false)
})
