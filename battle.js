function attack(i){
  const t=map[i];
  if(t.owner==="player")return;

  const atk=clan.race.attack+Math.floor(clan.gold/50);
  if(atk>t.defense){
    t.owner="player";
    clan.land++;
    clan.gold+=50;
    clan.food+=30;
    log("Territory conquered!");
  } else {
    clan.gold-=20;
    log("Attack failed!");
  }
  updateUI();
  renderMap();
}