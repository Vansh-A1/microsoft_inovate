import type { NextConfig } from 'next';
const config: NextConfig = { output: process.env.AP_BUILD_STANDALONE==='1'?'standalone':undefined, poweredByHeader: false, reactStrictMode: true,
 async headers(){return [{source:'/:path*',headers:[{key:'X-Content-Type-Options',value:'nosniff'},{key:'Referrer-Policy',value:'same-origin'},{key:'X-Frame-Options',value:'SAMEORIGIN'}]}]}
};
export default config;
