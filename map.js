let map = [];

function generateMap(){
  const types=["mine","forest","fort"];
  map=[];
  for(let i=0;i<100;i++){
    map.push({
      owner:i===55?"player":"enemy",
      type:types[i%3],
      defense:Math.floor(Math.random()*15)+10
    });
  }
  renderMap();
}

function renderMap(){
  mapDiv.innerHTML="";
  map.forEach((t,i)=>{
    const d=document.createElement("div");
    d.className=`cell ${t.owner} ${t.type}`;
    d.innerText=t.type[0].toUpperCase();
    d.onclick=()=>attack(i);
    mapDiv.appendChild(d);
  });
}