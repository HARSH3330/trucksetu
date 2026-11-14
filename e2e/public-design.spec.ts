import {expect,test} from '@playwright/test'

test.beforeEach(async({page})=>{
  await page.route('https://fonts.googleapis.com/**',route=>route.abort())
  await page.route('https://fonts.gstatic.com/**',route=>route.abort())
  // Only the external API boundary is simulated; exercise real rendered layouts.
  await page.route('**/api/v1/**',route=>route.fulfill({status:503,json:{detail:'Test dependency unavailable'}}))
})

test('mobile quote action is fully above fixed navigation even during a dependency outage',async({page})=>{
  await page.setViewportSize({width:390,height:844})
  await page.goto('/')
  const action=page.getByRole('button',{name:'Get transport quotes',exact:true})
  await expect(action).toBeVisible()
  await expect(page.getByRole('status').first()).toBeVisible()
  const actionBox=await action.boundingBox()
  const navBox=await page.locator('.mobile-nav').boundingBox()
  expect(actionBox!.y+actionBox!.height).toBeLessThanOrEqual(navBox!.y)
  await action.click()
  await expect(page.getByRole('dialog')).toBeVisible()
})

for(const width of [390,768,1440]){
  test(`public navigation stays usable without horizontal overflow at ${width}px`,async({page})=>{
    await page.setViewportSize({width,height:900})
    await page.goto('/')
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
    await page.getByRole('button',{name:'TransivoX',exact:true}).click()
    await expect(page.getByRole('heading',{name:'Transport quotes for your goods.'})).toBeVisible()
    const button=page.getByRole('button',{name:'Sign in',exact:true})
    await button.click()
    await expect(page.getByRole('dialog',{name:'Welcome back'})).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(button).toBeFocused()
  })
}
