setInterval(()=>{
  map.forEach(t=>{
    if(t.owner==="player" && Math.random()<0.01){
      t.owner="enemy";
      clan.land--;
      log("Enemy reclaimed land!");
    }
  });
  renderMap();
},5000);