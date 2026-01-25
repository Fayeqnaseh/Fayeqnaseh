races.forEach((r,i)=>{
  const o=document.createElement("option");
  o.value=i;
  o.innerText=r.name;
  raceSelect.appendChild(o);

  const c=document.createElement("div");
  c.className="character "+r.class;
  c.innerText=r.name;
  characters.appendChild(c);
});

function log(m){
  document.getElementById("log").innerText=m;
}