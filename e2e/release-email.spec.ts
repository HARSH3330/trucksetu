// All account API responses are simulated. No real email, auth or payment requests.
import {test,expect} from '@playwright/test'
for(const width of [1440,390])test('email links require explicit submission and remove fragment at '+width,async({page})=>{
 await page.setViewportSize({width,height:900})
 let submissions=0
 await page.route('**/*',async route=>{const url=new URL(route.request().url());if(url.hostname!=='127.0.0.1')return route.abort();if(url.pathname.includes('/api/v1/')){if(url.pathname.endsWith('/password-reset/confirm')){submissions++;expect(route.request().postDataJSON()).toMatchObject({email:'fictional@example.com',token:'a'.repeat(43)});return route.fulfill({json:{status:'password_reset'}})}return route.fulfill({status:401,json:{detail:'Synthetic signed-out account'}})}return route.continue()})
 await page.goto('/#account-reset?email=fictional%40example.com&token='+'a'.repeat(43))
 await expect(page.getByRole('dialog',{name:'Account recovery & verification'})).toBeVisible()
 await expect(page.getByLabel('Password reset token',{exact:true})).toHaveValue('a'.repeat(43))
 await expect(page).toHaveURL(/#home$/)
 expect(submissions).toBe(0)
 await page.getByLabel('New password',{exact:true}).fill('SyntheticLocalPassword123!')
 await page.getByRole('button',{name:'Set new password',exact:true}).click()
 await expect(page.getByRole('status')).toContainText('Previous sessions are invalidated')
 expect(submissions).toBe(1)
 await expect(page.getByLabel('Password reset token',{exact:true})).toHaveValue('')
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.getByRole('button',{name:'Close account help'}).click()
 await page.goto('/#account-verify?email=fictional%40example.com&code=123456')
 await expect(page.getByLabel('Email verification code',{exact:true})).toHaveValue('123456')
 await expect(page).toHaveURL(/#home$/)
})
