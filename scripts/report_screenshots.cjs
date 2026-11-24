/* Development-only capture of actual seeded pages for the report. */
const {chromium}=require('playwright-core');
const fs=require('node:fs');
const base=process.env.UI_BASE||'http://127.0.0.1:8003';
const out='docs/report_assets/screenshots';
const captures=[];
async function capture(page,name,route,role,scroll=0){
  const response=await page.goto(base+route,{waitUntil:'networkidle'});
  if(response.status()!==200)throw new Error(`${route}: ${response.status()}`);
  await page.evaluate(async()=>{await document.fonts.ready;for(const i of document.images)i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
  if(scroll)await page.evaluate(y=>window.scrollTo(0,y),scroll);
  await page.screenshot({path:`${out}/${name}.png`});
  const broken=await page.evaluate(()=>[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src));
  if(broken.length)throw new Error(`Broken image: ${broken}`);
  captures.push({file:name+'.png',route,role,viewport:page.viewportSize(),scale:2,scrollY:scroll});
}
async function signed(browser,user){
  const c=await browser.newContext({viewport:{width:1366,height:1000},deviceScaleFactor:2,serviceWorkers:'block'});
  const p=await c.newPage();await p.goto(base+'/accounts/login/');
  await p.locator('#id_username').fill(user);await p.locator('#id_password').fill('VirasatDemo2026!');
  await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('login'));
  return p;
}
(async()=>{
  fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--no-sandbox']});
  const context=await b.newContext({viewport:{width:1366,height:1000},deviceScaleFactor:2,serviceWorkers:'block'});
  const p=await context.newPage();
  for(const[name,route]of [['01-home','/'],['02-browse','/products/'],['03-product-detail','/product/1/madhubani-lotus-wall-painting/'],['04-register','/accounts/register/'],['05-login','/accounts/login/']])await capture(p,name,route,'Visitor');
  const artisan=await signed(b,'anita');
  await capture(artisan,'06-artisan-dashboard','/dashboard/','Artisan');
  await capture(artisan,'07-ai-describe','/dashboard/products/new/','Artisan');
  await capture(artisan,'08-ai-review','/dashboard/products/1/edit/','Artisan',650);
  const buyer=await signed(b,'neha');
  await buyer.goto(base+'/product/1/madhubani-lotus-wall-painting/');await buyer.locator('.detail-actions').getByRole('button',{name:'Add to cart',exact:true}).click();await buyer.waitForURL('**/cart/');
  for(const[name,route]of [['09-cart','/cart/'],['10-checkout','/checkout/'],['11-order-detail','/orders/VR000001/'],['12-requests','/requests/']])await capture(buyer,name,route,'Buyer');
  const mobileContext=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,serviceWorkers:'block'});
  const mobile=await mobileContext.newPage();
  await capture(mobile,'13-mobile-home','/','Visitor');await capture(mobile,'14-mobile-browse','/products/','Visitor');
  await buyer.setViewportSize({width:390,height:844});await capture(buyer,'15-mobile-checkout','/checkout/','Buyer');
  await b.close();fs.writeFileSync(out+'/screenshots.json',JSON.stringify(captures,null,2));console.log(`Captured ${captures.length} real screens.`);
})().catch(e=>{console.error(e);process.exit(1)});
