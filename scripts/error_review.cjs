/* Rendered templates are intercepted only in this development browser. */
const {chromium}=require('playwright-core');
const {default:AxeBuilder}=require('@axe-core/playwright');
const fs=require('node:fs');
(async()=>{
  const out='docs/ui_review/phase17';fs.mkdirSync(out,{recursive:true});
  const b=await chromium.launch({executablePath:'/usr/bin/google-chrome-stable',args:['--no-sandbox']});
  const results=[];
  for(const [width,height] of [[360,740],[390,844],[768,1024],[1366,768]]){
    const context=await b.newContext({viewport:{width,height},serviceWorkers:'block'});
    const p=await context.newPage();
    await p.route('**/__review/errors/*',r=>r.fulfill({contentType:'text/html',body:fs.readFileSync(`/tmp/opencode/error-previews/${r.request().url().split('/').pop()}.html`,'utf8')}));
    for(const code of [400,403,404,500]){
      await p.goto(`http://127.0.0.1:8003/__review/errors/${code}`,{waitUntil:'networkidle'});
      const scrollWidth=await p.evaluate(()=>document.documentElement.scrollWidth);
      const violations=width===390?(await new AxeBuilder({page:p}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze()).violations:[];
      results.push({code,width,height,scrollWidth,violations:violations.map(v=>v.id)});
      if(width===390)await p.screenshot({path:`${out}/error-${code}-390.png`,fullPage:true});
    }
    await p.context().close();
  }
  await b.close();fs.writeFileSync(out+'/errors.json',JSON.stringify(results,null,2));
  console.log(results);
  if(results.some(r=>r.scrollWidth>r.width||r.violations.length))process.exitCode=1;
})().catch(e=>{console.error(e);process.exit(1)});
