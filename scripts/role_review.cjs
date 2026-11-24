/* Development-only screenshots of signed-in pages using seeded accounts. */
const { chromium } = require('playwright-core');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.UI_BASE || 'http://127.0.0.1:8003';
const out = process.env.UI_OUT || 'docs/ui_review/before-phase16';
const sizes = process.env.UI_WIDTHS ? JSON.parse(process.env.UI_WIDTHS) : [[360,740],[768,1024],[1366,768]];
const roles = [
  ['anita', [['dashboard','/dashboard/'],['my-products','/dashboard/products/'],['describe','/dashboard/products/new/'],['review','/dashboard/products/1/edit/'],['fulfilment','/dashboard/orders/'],['matches','/requests/matches/'],['offers','/proposals/mine/'],['profile','/accounts/profile/'],['profile-edit','/accounts/profile/edit/']]],
  ['neha', [['buyer-detail','/product/1/madhubani-lotus-wall-painting/'],['cart','/cart/'],['checkout','/checkout/'],['orders','/orders/'],['order','/orders/VR000001/'],['requests','/requests/'],['request','/requests/1/'],['new-request','/requests/new/'],['my-requests','/requests/mine/'],['wishlist','/wishlist/']]],
  ['verifier', [['verification','/accounts/verify/']]],
];
(async () => {
  fs.mkdirSync(out, {recursive:true});
  const browser = await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--no-sandbox']});
  const issues=[];
  for(const [width,height] of sizes) for(const [user,routes] of roles) {
    const context=await browser.newContext({viewport:{width,height},serviceWorkers:'block'});
    const page=await context.newPage();
    page.on('pageerror',e=>issues.push(e.message));
    await page.goto(base+'/accounts/login/');
    await page.locator('#id_username').fill(user);
    await page.locator('#id_password').fill('VirasatDemo2026!');
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.waitForURL(url=>!url.pathname.includes('/login/'));
    if(user==='neha') {
      await page.goto(base+'/product/1/madhubani-lotus-wall-painting/');
      await page.locator('.detail-actions').getByRole('button',{name:'Add to cart',exact:true}).click();
      await page.waitForURL('**/cart/');
    }
    for(const [name,route] of routes) {
      const response=await page.goto(base+route,{waitUntil:'networkidle'});
      if(response.status()!==200) issues.push(`${name}-${width}: HTTP ${response.status()}`);
      await page.evaluate(async()=>{for(const i of document.images)i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));await document.fonts.ready;});
      const scroll=await page.evaluate(()=>document.documentElement.scrollWidth);
      if(scroll>width+1)issues.push(`${name}-${width}: overflow ${scroll}`);
      await page.screenshot({path:path.join(out,`${name}-${width}.png`),fullPage:true});
      console.log(`${user} ${name} ${width}: ${response.status()}, width ${scroll}`);
    }
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(out,'review.json'),JSON.stringify({sizes,roles,issues},null,2));
  console.log('ISSUES',issues);
  if(issues.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
