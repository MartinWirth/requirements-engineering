let schema={},spec=null,selectedType="Requirements",rows=[],tooltipTimer=null,tooltipMode="short";
const $=id=>document.getElementById(id),container=$("tableContainer"),message=$("message"),tooltip=$("tooltip"),filter=$("filter");
const label=name=>name.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
$("newProjectButton").addEventListener("click",()=>$("newProjectDialog").showModal());
const definition=()=>schema[selectedType];

async function loadProjectSpec(path){
  const response=await fetch("/api/project-spec?path="+encodeURIComponent(path));
  if(!response.ok)throw Error("Project specification could not be loaded.");
  spec=await response.json();
}
async function loadProjects(selectPath){
  const response=await fetch("/api/projects");
  if(!response.ok)throw Error("Project list could not be loaded.");
  const paths=await response.json(),select=$("projectSelect");
  const projects=await Promise.all(paths.map(async path=>({path,spec:await (await fetch("/api/project-spec?path="+encodeURIComponent(path))).json()})));
  select.replaceChildren(...projects.map(({path,spec})=>new Option(spec.title||path,path)));
  if(!paths.length)throw Error("No project specification found.");
  select.value=selectPath&&paths.includes(selectPath)?selectPath:paths[0];
  await loadProjectSpec(select.value);
}
async function newProject(){
  const dialog=$("newProjectDialog"),form=$("newProjectForm"),name=$("projectName").value.trim(),title=$("projectTitle").value.trim();
  if(!name||!form.reportValidity())return;
  dialog.close();
  const response=await fetch("/api/project-spec",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name,title})});
  if(!response.ok){const detail=await response.json().catch(()=>({}));return showError(detail.detail||"Project specification could not be created.");}
  await loadProjects((await response.json()).path);
  filter.value="";await loadTable();showMessage("Project specification created.");
}

async function init(){
  await loadProjects();
  const response=await fetch("/api/schema");
  if(!response.ok)throw Error("Model schema could not be loaded.");
  schema=await response.json();
  $("projectSelect").onchange=async e=>{try{await loadProjectSpec(e.target.value);filter.value="";await loadTable()}catch(error){showError(error.message)}};
  $("newProjectForm").addEventListener("submit",e=>{e.preventDefault();newProject()});
  $("modelSelect").onchange=e=>{selectedType=e.target.value;filter.value="";loadTable()};
  filter.oninput=()=>renderTable();
  $("tooltipMode").onchange=e=>{tooltipMode=e.target.value;hideTooltip()};
  $("newButton").onclick=()=>renderCreate();
  setActiveNav();await loadTable();
}
function setActiveNav(){$("modelSelect").value=selectedType;$("pageTitle").textContent=selectedType}
function visibleRows(){const q=filter.value.trim().toLowerCase();return q?rows.filter(row=>JSON.stringify(row).toLowerCase().includes(q)):rows}
function validate(value,field){
  const v=value.trim();
  if(!v)return field.required?{ok:false,message:"Required"}:{ok:true,value:null};
  if(field.kind==="enum")return field.values.includes(v)?{ok:true,value:v}:{ok:false,message:"Invalid value"};
  if(field.data_type==="int")return /^[-+]?\d+$/.test(v)?{ok:true,value:Number(v)}:{ok:false,message:"Integer expected"};
  if(field.data_type==="float"){const n=v.replace(",","." );return /^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(n)?{ok:true,value:Number(n)}:{ok:false,message:"Number expected"}}
  if(field.data_type==="bool")return ["true","false"].includes(v.toLowerCase())?{ok:true,value:v.toLowerCase()==="true"}:{ok:false,message:"true or false expected"};
  if(field.kind==="json")try{const value=JSON.parse(v);if(field.data_type==="list"&&!Array.isArray(value))return{ok:false,message:"JSON list expected"};if(field.data_type==="dict"&&(value===null||Array.isArray(value)||typeof value!=="object"))return{ok:false,message:"JSON object expected"};return{ok:true,value}}catch{return{ok:false,message:"Valid JSON expected"}}
  return{ok:true,value:v};
}
function createEditor(field,value=""){
  if(field.kind==="enum"){const el=document.createElement("select");el.add(new Option("— select —",""));field.values.forEach(v=>el.add(new Option(v,v)));el.value=value??"";return el}
  const el=document.createElement("textarea");el.value=value==null?"":typeof value==="object"?JSON.stringify(value):String(value);
  el.rows=field.data_type==="list"||field.data_type==="dict"||String(field.name).includes("description")||String(field.name).includes("statement")?3:1;
  el.placeholder=field.data_type==="list"?'["value 1", "value 2"]':field.data_type==="dict"?'{ "key": "value" }':field.data_type||"";
  return el;
}
function addHeaderTooltip(th,field){th.className="help-header";th.title=field.summary;const text=document.createElement("span");text.className="header-label";text.textContent=label(field.name);th.append(text);th.onmouseenter=e=>showTooltip(e,field);th.onmousemove=moveTooltip;th.onmouseleave=scheduleHide}
function actionTooltip(event,action,def,row){
  clearTimeout(tooltipTimer);tooltip.replaceChildren();const title=document.createElement("strong");title.textContent=action+" "+selectedType.replace(/s$/,"");tooltip.append(title);
  if(tooltipMode==="short"){const text=document.createElement("div");text.textContent="Edit this "+selectedType.toLowerCase().replace(/s$/,"")+".";tooltip.append(text);const link=document.createElement("a");link.href="https://cpre.ireb.org/en/downloads-and-resources/glossary";link.target="_blank";link.rel="noopener noreferrer";link.textContent="Open IREB documentation";tooltip.append(document.createElement("br"),link)}
  else if(tooltipMode==="api"){const code=document.createElement("code");code.textContent=action==="Modify"?"PUT "+def.endpoint+"/"+row.id:"POST "+def.endpoint;tooltip.append(code)}
  else{const desc=document.createElement("div");desc.textContent=action+" "+selectedType.toLowerCase().replace(/s$/,"")+". The action operates on the complete model element and preserves its relationships.";tooltip.append(desc);const deps=def.fields.filter(f=>/(related|depends|conflicts|includes|extends|generalizes|actor|parent|source_id|target_id)/i.test(f.name));if(deps.length){const heading=document.createElement("div");heading.innerHTML="<strong>Dependencies</strong>";tooltip.append(heading);deps.forEach(f=>{const v=row?.[f.name];if(v==null||v===""||(Array.isArray(v)&&!v.length))return;const d=document.createElement("div");d.textContent=label(f.name)+": "+(typeof v==="object"?JSON.stringify(v):v);tooltip.append(d)})}}
  tooltip.hidden=false;moveTooltip(event);
}
function showTooltip(event,field){clearTimeout(tooltipTimer);tooltip.replaceChildren();const title=document.createElement("strong"),summary=document.createElement("div"),link=document.createElement("a");title.textContent=label(field.name);summary.textContent=field.summary;link.href=field.documentation_url;link.target="_blank";link.rel="noopener noreferrer";link.textContent="Open IREB documentation";tooltip.append(title,summary,document.createElement("br"),link);tooltip.hidden=false;moveTooltip(event)}
function moveTooltip(e){if(tooltip.hidden)return;tooltip.style.left=Math.max(8,Math.min(e.clientX+12,innerWidth-tooltip.offsetWidth-12))+"px";tooltip.style.top=Math.max(8,Math.min(e.clientY+14,innerHeight-tooltip.offsetHeight-12))+"px"}
function scheduleHide(){clearTimeout(tooltipTimer);tooltipTimer=setTimeout(hideTooltip,250)}
function hideTooltip(){clearTimeout(tooltipTimer);tooltip.hidden=true}
tooltip.onmouseenter=()=>clearTimeout(tooltipTimer);tooltip.onmouseleave=scheduleHide;
function editorRow(def,row,isNew=false){
  const tr=document.createElement("tr");tr.className=isNew?"new-row":"edit-row";const editors=[],action=document.createElement("td");action.className="action-cell";
  const save=button(isNew?"Create":"Save"),cancel=button("Cancel");save.onclick=()=>saveRow(def,row,editors,isNew,save);cancel.onclick=()=>renderTable();action.append(save,cancel);tr.append(action);
  def.fields.forEach(field=>{const td=document.createElement("td"),editor=createEditor(field,isNew?"":row[field.name]);if(field.name==="id"&&!isNew)editor.disabled=true;if(field.name==="id"&&isNew){editor.disabled=true;editor.placeholder="auto-generated"}const status=document.createElement("div");status.className="status";td.append(editor,status);const check=()=>{const result=validate(editor.value,field);editor.classList.toggle("invalid",!result.ok);status.className="status "+(result.ok?"valid":"invalid");status.textContent=result.ok?"":result.message;return result};editor.oninput=editor.onchange=check;editors.push({field,editor,check});tr.append(td)});return tr;
}
function button(text){const b=document.createElement("button");b.textContent=text;return b}
async function saveRow(def,row,editors,isNew,saveButton){
  const payload={};let valid=true;editors.forEach(({field,editor,check})=>{const result=check();if(!result.ok)valid=false;else if(field.name!=="id"&&result.value!=null)payload[field.name]=result.value});if(!valid)return showError("Please correct the highlighted values.");saveButton.disabled=true;
  try{const url=isNew?def.endpoint:def.endpoint+"/"+encodeURIComponent(row.id),method=isNew?"POST":"PUT";const response=await fetch(url,{method,headers:{"Content-Type":"application/json"},body:JSON.stringify(isNew?payload:{...payload,id:row.id})});if(!response.ok){const detail=await response.json().catch(()=>({}));throw Error(detail.detail||"Save failed")}showMessage(isNew?"Element created.":"Element updated.");await loadTable()}catch(error){showError(error.message);saveButton.disabled=false}
}
function renderCreate(){container.replaceChildren();const table=document.createElement("table"),head=document.createElement("tr"),th=document.createElement("th");th.textContent="Action";head.append(th);definition().fields.forEach(field=>{const x=document.createElement("th");addHeaderTooltip(x,field);head.append(x)});const thead=table.createTHead();thead.append(head);const body=table.createTBody();body.append(editorRow(definition(),{},true));container.append(table)}
function renderTable(){
  container.replaceChildren();const def=definition(),table=document.createElement("table"),thead=table.createTHead(),head=thead.insertRow(),actionTh=document.createElement("th");actionTh.textContent="Action";head.append(actionTh);def.fields.forEach(field=>{const th=document.createElement("th");addHeaderTooltip(th,field);head.append(th)});
  const body=table.createTBody(),visible=visibleRows();visible.forEach(row=>{const tr=body.insertRow(),action=tr.insertCell();action.className="action-cell";const modify=button("Modify");modify.onclick=()=>tr.replaceWith(editorRow(def,row));modify.onmouseenter=e=>actionTooltip(e,"Modify",def,row);modify.onmousemove=moveTooltip;modify.onmouseleave=scheduleHide;action.append(modify);def.fields.forEach(field=>{const td=tr.insertCell(),value=row[field.name];td.textContent=typeof value==="object"?JSON.stringify(value):value??"";if(field.name==="id")td.className="id-cell"});tr.ondblclick=()=>tr.replaceWith(editorRow(def,row))});
  if(!visible.length){const tr=body.insertRow(),td=tr.insertCell();td.colSpan=def.fields.length+1;td.className="empty";td.textContent="No elements."}container.append(table);
}
async function loadTable(){
  const response=await fetch(definition().endpoint);
  if(!response.ok)return showError("Could not load "+selectedType+".");
  rows=await response.json();
  const key={Requirements:"requirements","User Stories":"user_stories","Use Cases":"use_cases",Actors:"actors",Traceability:"traceability","Work Items":"work_items","Test Cases":"test_cases"}[selectedType];
  if(key&&spec?.project_data?.[key])rows=spec.project_data[key];
  setActiveNav();renderTable();
}
function showMessage(text){if(message){message.textContent=text;message.className="success"}}function showError(text){if(message){message.textContent=text;message.className="error"}else console.error(text)}
init().catch(error=>showError(error.message));