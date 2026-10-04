from app.domain.extraction import ExtractionObservationState as State
DESCRIPTIONS={
'vendor_name':'seller/supplier company name in the invoice heading (not the customer)',
'vendor_address':'printed seller/supplier street, city and postal address (not Bill To or Ship To)',
'customer_bill_to':'printed Bill To customer name and billing address',
'bill_to_address':'ALL printed address lines in the Bill To block, including street, city, state and postal code; do not use Ship To or seller address',
'ship_to_address':'ALL printed address lines in the Ship To block, including street, city, state and postal code; do not use Bill To or seller address',
'invoice_number':'identifier explicitly labeled Invoice # or Invoice Number',
'receipt_number':'receipt identifier only for a receipt, not an invoice number',
'invoice_date':'date printed next to Invoice Date; preserve the printed order, never guess locale',
'due_date':'date printed next to Due Date; preserve the printed order',
'po_reference':'purchase order reference printed next to P.O.#, PO, or Purchase Order',
'currency':'explicit printed currency code or symbol; dollar symbol alone is ambiguous, never infer USD from address',
'subtotal_amount':'document Subtotal amount',
'document_discount_amount':'document discount only when explicitly printed; never invent zero',
'shipping_amount':'document Shipping, Delivery or Freight charge only if explicitly printed; never invent zero',
'other_charges_amount':'document other charge only if explicitly printed; never invent zero',
'tax_amount':'document tax amount (not percentage) for headers, but ONLY the selected item row tax amount for a row; never copy a document-level tax into a row',
'payment_terms':'printed payment terms sentence',
'payment_account_token':'printed payment account identifier only; never infer an account',
'tax_basis':'explicit tax-exclusive or tax-inclusive statement only; a tax number is not a tax basis',
'local_timezone':'explicit timezone label only; never infer from city',
'category':'explicit expense category label only; invoice is a document type, not expense category',
'receipt_type':'explicit receipt type for an employee receipt only',
'expense_date':'date explicitly shown on an employee receipt only',
'description':'description of ONLY the selected item row',
'quantity':'quantity (QTY) of ONLY the selected item row',
'unit_price':'UNIT PRICE or RATE of ONLY the selected item row, not the line amount',
'amount':'printed AMOUNT or LINE TOTAL of ONLY the selected item row. Never return SUBTOTAL, document TAX or document TOTAL',
'net_amount':'printed NET or AMOUNT of ONLY the selected item row. Never return SUBTOTAL, document TAX or document TOTAL',
'gross_amount':'explicitly labeled GROSS or tax-inclusive total of ONLY the selected item row. If only AMOUNT is printed and gross is not distinguished, return null. Never return the document TOTAL',
'discount_amount':'discount explicitly printed for ONLY the selected item row; if absent return null, not zero',
'tax_rate':'tax rate explicitly printed for ONLY the selected item row; document Sales Tax is not a row tax rate; if absent return null',
'uom':'explicitly printed unit of measure for ONLY the selected item row; if absent return null',
'row_count':'count of visible item rows in the item table on THIS page, excluding column headings, subtotal, tax, totals, addresses and payment terms'
}
def questions(fields):
 out={}
 for f in fields:
  name=f+'_raw';desc=DESCRIPTIONS.get(f,f.replace('_',' '))
  out[name]={'type':['string','null'],'instructions':f'Copy {desc} exactly as printed. Return only its literal text as a string or null when absent/unreadable. Do not calculate, translate, infer, fill defaults or copy another field. Money and quantity remain strings.','thinking':False}
  out[f+'_state']={'type':'string','enum':[s.value for s in State],'depends_on':[name],'instructions':f'Assess evidence for {desc}. PRESENT means the requested value is actually readable and the raw string is grounded in this exact field/row. MISSING means it is not printed. ILLEGIBLE means it exists but cannot be read. AMBIGUOUS means multiple meanings/values or uncertain assignment. NOT_APPLICABLE only if explicitly stated not applicable on the document. A printed P.O.# is PRESENT. Never mark a guessed or unrelated value PRESENT.','thinking':False}
 return out
