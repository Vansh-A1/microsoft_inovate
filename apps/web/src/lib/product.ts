/** Build-time public presentation only; never a business policy or authority. */
const configuredName=process.env.NEXT_PUBLIC_PRODUCT_NAME?.trim();
export const PRODUCT_NAME=configuredName&&configuredName.length<=48?configuredName:'ClearLedger';
