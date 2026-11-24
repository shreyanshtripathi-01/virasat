/* Development-only responsive and WCAG checks using real rendered pages. */
const {chromium}=require('playwright-core');
const {default:AxeBuilder}=require('@axe-core/playwright');
const fs=require('node:fs');
const base=process.env.UI_BASE||'http://127.0.0.1:8003';
const out=process.env.UI_OUT||'docs/ui_review/phase17';
const sizes=[[360,740],[390,844],[768,1024],[1366,768]];
const groups=[
  [null,['/','/products/','/product/1/madhubani-lotus-wall-painting/','/accounts/login/','/accounts/register/','/craft/madhubani/','/category/accessories/','/artisans/3/','/about/','/impact/','/offline/','/products/?q=not-a-real-piece','/products/?q=art&craft=1']],
  ['anita',['/dashboard/','/dashboard/products/','/dashboard/products/new/','/dashboard/products/1/edit/','/dashboard/products/2/delete/','/dashboard/orders/','/requests/matches/','/proposals/mine/','/requests/1/propose/','/accounts/profile/','/accounts/profile/edit/']],
  ['neha',['/product/1/madhubani-lotus-wall-painting/','/cart/','/checkout/','/orders/','/orders/VR000001/','/requests/','/requests/1/','/requests/new/','/requests/mine/','/wishlist/']],
  ['verifier',['/accounts/verify/']],
];
(async()=>{
  fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--no-sandbox']});
  const rows=[];
  for(const [width,height] of sizes)for(const [user,routes] of groups){
    const context=await b.newContext({viewport:{width,height},serviceWorkers:'block'});
    const p=await context.newPage();
    if(user){
      await p.goto(base+'/accounts/login/');
      await p.locator('#id_username').fill(user);await p.locator('#id_password').fill('VirasatDemo2026!');
      await p.getByRole('button',{name:'Sign in',exact:true}).click();await p.waitForURL(u=>!u.pathname.includes('/login/'));
      if(user==='neha'){await p.goto(base+'/product/1/madhubani-lotus-wall-painting/');await p.locator('.detail-actions').getByRole('button',{name:'Add to cart',exact:true}).click();await p.waitForURL('**/cart/');}
    }
    for(const route of routes){
      const response=await p.goto(base+route,{waitUntil:'networkidle'});
      const measured=await p.evaluate(()=>{
        const visible=e=>e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
        const ids=new Set([...document.querySelectorAll('[id]')].map(e=>e.id));
        return {
          scrollWidth:document.documentElement.scrollWidth,
          imagesMissingDimensions:[...document.images].filter(e=>!e.hasAttribute('width')||!e.hasAttribute('height')).map(e=>e.getAttribute('src')),
          smallInputs:[...document.querySelectorAll('input:not([type=hidden]),select,textarea')].filter(e=>visible(e)&&!['radio','checkbox','file'].includes(e.type)&&parseFloat(getComputedStyle(e).fontSize)<16).map(e=>e.id),
          brokenDescriptions:[...document.querySelectorAll('[aria-describedby]')].flatMap(e=>e.getAttribute('aria-describedby').split(' ').filter(id=>!ids.has(id))),
        };
      });
      const row={user:user||'visitor',route,width,height,status:response.status(),...measured};
      if(width===390&&!process.env.SKIP_AXE){
        const result=await new AxeBuilder({page:p}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
        row.violations=result.violations.map(v=>({id:v.id,impact:v.impact,help:v.help,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
      }
      rows.push(row);
      if(width===390&&['/','/dashboard/','/cart/','/checkout/','/accounts/register/'].includes(route)){
        await p.evaluate(async()=>{for(const i of document.images)i.loading='eager';await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));});
        const name=route.replaceAll('/','-').replace(/^-|-$/g,'')||'home';
        await p.screenshot({path:`${out}/${user||'visitor'}-${name}-390.png`,fullPage:true});
      }
      console.log(`${row.user} ${width} ${route}: ${row.status} width=${row.scrollWidth} axe=${row.violations?.length||0}`);
    }
    await context.close();
  }
  await b.close();
  fs.writeFileSync(out+'/audit.json',JSON.stringify(rows,null,2));
  const failures=rows.filter(r=>r.status!==200||r.scrollWidth>r.width+1||r.smallInputs.length||r.imagesMissingDimensions.length||r.brokenDescriptions.length||r.violations?.length);
  console.log(`Checked ${rows.length} page/size combinations; ${failures.length} need attention.`);
  if(failures.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
