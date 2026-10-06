let schema={},selectedType="Requirements",rows=[],tooltipTimer=null;
const $=id=>document.getElementById(id),container=$("tableContainer"),message=$("message"),tooltip=$("tooltip"),filter=$("filter");
const label=name=>name.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
const definition=()=>schema[selectedType];

async function init(){
  const response=await fetch("/api/schema");
  if(!response.ok) throw Error("Model schema could not be loaded.");
  schema=await response.json();
  document.querySelectorAll("#navigation button").forEach(button=>{
    button.onclick=()=>{selectedType=button.dataset.type;filter.value="";setActiveNav();loadTable()};
  });
  filter.oninput=()=>renderTable();
  $("newButton").onclick=()=>renderCreate();
  setActiveNav(); await loadTable();
}
function setActiveNav(){
  document.querySelectorAll("#navigation button").forEach(b=>b.classList.toggle("active",b.dataset.type===selectedType));
  $("pageTitle").textContent=selectedType;
}
function visibleRows(){
  const q=filter.value.trim().toLowerCase();
  return q?rows.filter(row=>JSON.stringify(row).toLowerCase().includes(q)):rows;
}
function validate(value,field){
  const v=value.trim();
  if(!v)return field.required?{ok:false,message:"Required"}:{ok:true,value:null};
  if(field.kind==="enum")return field.values.includes(v)?{ok:true,value:v}:{ok:false,message:"Invalid value"};
  if(field.data_type==="int")return /^[-+]?\d+$/.test(v)?{ok:true,value:Number(v)}:{ok:false,message:"Integer expected"};
  if(field.data_type==="float"){const n=v.replace(",",".");return /^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(n)?{ok:true,value:Number(n)}:{ok:false,message:"Number expected"}}
  if(field.data_type==="bool")return ["true","false"].includes(v.toLowerCase())?{ok:true,value:v.toLowerCase()==="true"}:{ok:false,message:"true or false expected"};
  if(field.kind==="json")try{const value=JSON.parse(v);if(field.data_type==="list"&&!Array.isArray(value))return{ok:false,message:"JSON list expected"};if(field.data_type==="dict"&&(value===null||Array.isArray(value)||typeof value!=="object"))return{ok:false,message:"JSON object expected"};return{ok:true,value}}catch{return{ok:false,message:"Valid JSON expected"}}
  return{ok:true,value:v};
}
function createEditor(field,value=""){
  if(field.kind==="enum"){const el=document.createElement("select");el.add(new Option("— select —",""));field.values.forEach(v=>el.add(new Option(v,v)));el.value=value??"";return el}
  const el=document.createElement("textarea");el.value=value==null?"":typeof value==="object"?JSON.stringify(value):String(value);
  el.rows=field.data_type==="list"||field.data_type==="dict"||String(field.name).includes("description")||String(field.name).includes("statement")?3:1;
  el.placeholder=field.data_type==="list"?'["value 1", "value 2"]':field.data_type==="dict"?'{"key":"value"}':field.data_type||"";
  return el;
}
function addHeaderTooltip(th,field){
  th.className="help-header";th.title=field.summary;
  const text=document.createElement("span");text.className="header-label";text.textContent=label(field.name);th.append(text);
  th.onmouseenter=e=>showTooltip(e,field);th.onmousemove=moveTooltip;th.onmouseleave=scheduleHide;
}
function showTooltip(event,field){
  clearTimeout(tooltipTimer);tooltip.replaceChildren();
  const title=document.createElement("strong"),summary=document.createElement("div"),link=document.createElement("a");
  title.textContent=label(field.name);summary.textContent=field.summary;link.href=field.documentation_url;link.target="_blank";link.rel="noopener noreferrer";link.textContent="Open IREB documentation";
  tooltip.append(title,summary,document.createElement("br"),link);tooltip.hidden=false;moveTooltip(event);
}
function moveTooltip(e){if(tooltip.hidden)return;tooltip.style.left=Math.max(8,Math.min(e.clientX+12,innerWidth-tooltip.offsetWidth-12))+"px";tooltip.style.top=Math.max(8,Math.min(e.clientY+14,innerHeight-tooltip.offsetHeight-12))+"px"}
function scheduleHide(){clearTimeout(tooltipTimer);tooltipTimer=setTimeout(hideTooltip,250)}
function hideTooltip(){clearTimeout(tooltipTimer);tooltip.hidden=true}
tooltip.onmouseenter=()=>clearTimeout(tooltipTimer);tooltip.onmouseleave=scheduleHide;

function editorRow(def,row,isNew=false){
  const tr=document.createElement("tr");tr.className=isNew?"new-row":"edit-row";const editors=[];
  const action=document.createElement("td");action.className="action-cell";
  const save=button(isNew?"Create":"Save"),cancel=button("Cancel");
  save.onclick=()=>saveRow(def,row,editors,isNew,save);cancel.onclick=()=>renderTable();
  action.append(save,cancel);tr.append(action);
  def.fields.forEach(field=>{
    const td=document.createElement("td"),editor=createEditor(field,isNew?"":row[field.name]);
    if(field.name==="id"&&!isNew)editor.disabled=true;
    if(field.name==="id"&&isNew){editor.disabled=true;editor.placeholder="auto-generated";}
    const status=document.createElement("div");status.className="status";td.append(editor,status);
    const check=()=>{const result=validate(editor.value,field);editor.classList.toggle("invalid",!result.ok);status.className="status "+(result.ok?"valid":"invalid");status.textContent=result.ok?"":result.message;return result};
    editor.oninput=editor.onchange=check;editors.push({field,editor,check});tr.append(td);
  });
  return tr;
}
function button(text){const b=document.createElement("button");b.textContent=text;return b}
async function saveRow(def,row,editors,isNew,saveButton){
  const payload={};let valid=true;
  editors.forEach(({field,editor,check})=>{const result=check();if(!result.ok)valid=false;else if(field.name!=="id"&&result.value!=null)payload[field.name]=result.value});
  if(!valid)return showError("Please correct the highlighted values.");
  saveButton.disabled=true;
  try{
    const url=isNew?def.endpoint:def.endpoint+"/"+encodeURIComponent(row.id),method=isNew?"POST":"PUT";
    const response=await fetch(url,{method,headers:{"Content-Type":"application/json"},body:JSON.stringify(isNew?payload:{...payload,id:row.id})});
    if(!response.ok){const detail=await response.json().catch(()=>({}));throw Error(detail.detail||"Save failed")}
    showMessage(isNew?"Element created.":"Element updated.");await loadTable();
  }catch(error){showError(error.message);saveButton.disabled=false}
}
function renderCreate(){container.replaceChildren();const table=document.createElement("table"),head=document.createElement("tr"),th=document.createElement("th");th.textContent="Action";head.append(th);definition().fields.forEach(field=>{const x=document.createElement("th");addHeaderTooltip(x,field);head.append(x)});table.append(Object.assign(document.createElement("thead"),{innerHTML:""}));table.tHead.append(head);const body=table.createTBody();body.append(editorRow(definition(),{},true));container.append(table)}
function renderTable(){
  container.replaceChildren();const def=definition(),table=document.createElement("table"),thead=table.createTHead(),head=thead.insertRow(),actionTh=document.createElement("th");
  actionTh.textContent="Action";head.append(actionTh);def.fields.forEach(field=>{const th=document.createElement("th");addHeaderTooltip(th,field);head.append(th)});
  const body=table.createTBody(),visible=visibleRows();
  visible.forEach(row=>{
    const tr=body.insertRow(),action=tr.insertCell();action.className="action-cell";const modify=button("Modify");
    modify.onclick=()=>tr.replaceWith(editorRow(def,row));action.append(modify);
    def.fields.forEach(field=>{const td=tr.insertCell(),value=row[field.name];td.textContent=typeof value==="object"?JSON.stringify(value):value??"";if(field.name==="id")td.className="id-cell"});
    tr.ondblclick=()=>tr.replaceWith(editorRow(def,row));
  });
  if(!visible.length){const tr=body.insertRow(),td=tr.insertCell();td.colSpan=def.fields.length+1;td.className="empty";td.textContent="No elements."; }
  container.append(table);
}
async function loadTable(){
  const response=await fetch(definition().endpoint);
  if(!response.ok)return showError("Could not load "+selectedType+".");
  rows=await response.json();setActiveNav();renderTable();
}
function showMessage(text){message.textContent=text;message.className="success"}function showError(text){message.textContent=text;message.className="error"}
init().catch(error=>showError(error.message));
