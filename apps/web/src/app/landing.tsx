'use client';
import Link from 'next/link';
import {PRODUCT_NAME} from '@/lib/product';

export function Landing(){
 return <div className="landing">
  <a className="skip" href="#main">Skip to content</a>
  <header className="landing-nav"><Link className="brand" href="/welcome"><span className="brand-mark" aria-hidden="true">{PRODUCT_NAME.slice(0,1).toLowerCase()}</span>{PRODUCT_NAME}</Link><nav aria-label="Product navigation"><a href="#how-it-works">How it works</a><Link className="button secondary" href="/login">Open your workspace</Link></nav></header>
  <main id="main" className="landing-main">
   <section className="landing-hero"><div className="landing-copy"><h1>Less invoice fuss.<br/>More clarity.</h1><p>Bring a document. Follow the evidence. Know your next step.</p><Link className="button" href="/login">Get started</Link></div>
    <figure className="product-proof"><div className="proof-paper"><img src="/ui/verified-fictional-result.png" width="964" height="282" alt="Actual fictional invoice result: Ready for processing after its finance checks passed"/></div><figcaption>A verified fictional example. Every outcome comes from its evidence and configured controls.</figcaption></figure>
   </section>
   <section id="how-it-works" className="landing-story"><h2>A clear path through the paperwork.</h2><ol><li><span>1</span><div><h3>Start with a file</h3><p>Upload an invoice or receipt. Its original stays intact.</p></div></li><li><span>2</span><div><h3>Check what’s uncertain</h3><p>See printed facts beside their source. Confirm or correct what needs attention.</p></div></li><li><span>3</span><div><h3>Take the next step</h3><p>Get one outcome, with the reason and action it needs.</p></div></li></ol></section>
   <section className="landing-admin"><div><h2>Your rules. A traceable history.</h2><p>Manage allowances, people, approvals and budgets in a separate Admin Console. Policy changes create versions; earlier decisions stay available.</p></div><Link className="text-link" href="/login">Choose Admin access</Link></section>
   <p className="workspace-limit">This local workspace uses fictional identities and sample policies. It does not execute payments or provide production identity or malware protection.</p>
  </main><footer className="landing-footer"><span>{PRODUCT_NAME}</span><span>Clear decisions, with evidence.</span></footer>
 </div>;
}
