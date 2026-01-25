let clan = null;

function createClan(){
  const name = clanName.value;
  const race = races[raceSelect.value];

  clan = {
    name,
    race,
    land:1,
    gold:100,
    food:100,
    alliance:null
  };

  createClan.style.display="none";
  game.style.display="block";
  updateUI();
  generateMap();
}

function updateUI(){
  clanInfo.innerText =
   `${clan.name} | ${clan.race.name} | Land:${clan.land} | Gold:${clan.gold} | Food:${clan.food}`;
}