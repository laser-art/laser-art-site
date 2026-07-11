(()=>{
const css=`
#motionStage{height:210px;margin:14px 0 4px;border-radius:18px;background:linear-gradient(180deg,#242424,#111);position:relative;overflow:hidden;border:1px solid #3a3a3a}
#bag{position:absolute;right:16%;top:20px;width:58px;height:145px;border-radius:28px;background:#8b1e24;border:5px solid #b94a50;transform-origin:50% 0}
#fighter{position:absolute;left:18%;bottom:18px;width:120px;height:160px}
.head,.body,.limb{position:absolute;background:#f0b429}.head{width:34px;height:34px;border-radius:50%;left:42px;top:4px}.body{width:24px;height:64px;border-radius:14px;left:47px;top:39px}.limb{height:14px;border-radius:9px;transform-origin:8px 7px}.armL{width:62px;left:42px;top:48px;transform:rotate(150deg)}.armR{width:62px;left:58px;top:49px;transform:rotate(25deg)}.legL{width:72px;left:39px;top:96px;transform:rotate(115deg)}.legR{width:72px;left:56px;top:96px;transform:rotate(62deg)}
#fighter.jab .armL{animation:jab .6s infinite}#fighter.cross .armR{animation:cross .7s infinite}#fighter.hook .armL{animation:hook .8s infinite}#fighter.lowkick .legR{animation:lowkick .9s infinite}#fighter.frontkick .legL{animation:frontkick .9s infinite}#fighter.knee .legR{animation:knee .8s infinite}#fighter.slip{animation:slip .8s infinite}#fighter.squat{animation:squat 1.1s infinite}#fighter.pushup{transform:rotate(90deg);transform-origin:center;animation:pushup 1.1s infinite}#fighter.move{animation:move 1.4s infinite alternate}
#bag.hit{animation:baghit .5s infinite alternate}
@keyframes jab{0%,100%{transform:rotate(150deg)}50%{transform:rotate(8deg);width:88px}}@keyframes cross{0%,100%{transform:rotate(25deg)}50%{transform:rotate(-2deg);width:92px}}@keyframes hook{0%,100%{transform:rotate(150deg)}50%{transform:rotate(75deg);left:62px}}@keyframes lowkick{0%,100%{transform:rotate(62deg)}50%{transform:rotate(-8deg);width:92px}}@keyframes frontkick{0%,100%{transform:rotate(115deg)}50%{transform:rotate(12deg);width:96px}}@keyframes knee{0%,100%{transform:rotate(62deg)}50%{transform:rotate(-55deg);left:70px}}@keyframes slip{0%,100%{transform:translateX(0) rotate(0)}50%{transform:translateX(-16px) rotate(-10deg)}}@keyframes squat{0%,100%{transform:translateY(0)}50%{transform:translateY(34px)}}@keyframes pushup{0%,100%{transform:rotate(90deg) translateX(0)}50%{transform:rotate(90deg) translateX(18px)}}@keyframes move{from{left:8%}to{left:34%}}@keyframes baghit{from{transform:rotate(-2deg)}to{transform:rotate(5deg)}}
#drillLabel{position:absolute;left:12px;bottom:10px;background:#000b;padding:6px 9px;border-radius:10px;font-size:12px;font-weight:800}
`;
const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
const card=document.querySelector('#workout .card');const stage=document.createElement('div');stage.id='motionStage';stage.innerHTML='<div id="fighter"><div class="head"></div><div class="body"></div><div class="limb armL"></div><div class="limb armR"></div><div class="limb legL"></div><div class="limb legR"></div></div><div id="bag"></div><div id="drillLabel">Démonstration</div>';
card.insertBefore(stage,document.getElementById('timer'));
const drillSets={
 debutant:[
  {name:'Technique jab-direct',focus:'Précision et retour en garde',commands:['Jab seul','Jab, direct','Jab, direct, garde','Double jab, direct']},
  {name:'Poings et low kick',focus:'Termine chaque série par le tibia',commands:['Jab, direct, low kick arrière','Jab, low kick avant','Direct, crochet avant, low kick arrière']},
  {name:'Genoux au sac',focus:'Contrôle le sac puis replace-toi',commands:['Jab, direct, genou arrière','Deux genoux alternés','Direct, crochet, genou arrière']},
  {name:'Déplacements',focus:'Frappe puis sors de l’axe',commands:['Jab, pas à gauche, direct','Jab, direct, pas à droite','Double jab en avançant, recule']},
  {name:'Vitesse',focus:'Frappes légères et rapides',commands:['Jab-direct en continu','Crochets alternés','10 secondes très rapide, puis garde']}
 ],
 intermediaire:[
  {name:'Corps-tête',focus:'Change de hauteur sans te relever',commands:['Jab tête, direct corps, crochet tête','Direct corps, crochet tête, low kick','Jab corps, direct tête, crochet avant']},
  {name:'Défense-riposte',focus:'Imagine le retour adverse',commands:['Jab, direct, esquive, crochet','Blocage, direct, crochet, low kick','Pas arrière, direct, genou']},
  {name:'Kicks en chaîne',focus:'Garde haute pendant les coups de pied',commands:['Jab, direct, low kick arrière','Front kick avant, direct, low kick arrière','Direct, crochet, high kick contrôlé']},
  {name:'Pression',focus:'Avance sans te jeter',commands:['Double jab, direct','Jab, crochet, direct, low kick','Trois frappes, angle, deux frappes']},
  {name:'Puissance propre',focus:'70 %, équilibre parfait',commands:['Direct puissant, crochet, low kick','Jab, direct, genou arrière','Crochet avant, crochet arrière, low kick']}
 ],
 avance:[
  {name:'Combinaisons longues',focus:'Reste relâché au milieu de la série',commands:['Double jab, direct corps, crochet tête, low kick','Front kick, jab, direct, crochet, genou','Jab, direct, crochet arrière, crochet avant, low kick']},
  {name:'Contre et angle',focus:'Fais manquer puis réponds',commands:['Esquive extérieure, direct, crochet, low kick','Pas arrière, direct, genou, angle','Blocage low kick, direct, crochet']},
  {name:'Rythme cassé',focus:'Lent-lent-vite',commands:['Jab lent, direct lent, crochet-low kick rapide','Double jab léger, direct puissant','Feinte jab, direct, crochet, genou']},
  {name:'Round combat',focus:'Alterner attaque, défense et déplacement',commands:['Pression 15 secondes','Défense et contre 15 secondes','Sorties d’angle et reprises']},
  {name:'Finisher',focus:'Vitesse maximale avec technique',commands:['Rafale poings 10 secondes','Low kicks alternés 10 secondes','Genoux alternés 10 secondes']}
 ]
};
function motionFor(t){t=(t||'').toLowerCase();if(t.includes('low kick')||t.includes('high kick')||t.includes('kick'))return'lowkick';if(t.includes('front kick'))return'frontkick';if(t.includes('genou'))return'knee';if(t.includes('crochet'))return'hook';if(t.includes('esquive')||t.includes('blocage'))return'slip';if(t.includes('pas')||t.includes('angle')||t.includes('avance')||t.includes('recule'))return'move';if(t.includes('squat'))return'squat';if(t.includes('pompe'))return'pushup';if(t.includes('direct'))return'cross';return'jab'}
function animate(t){const f=document.getElementById('fighter'),b=document.getElementById('bag');f.className='';void f.offsetWidth;f.classList.add(motionFor(t));b.className=(/jab|direct|crochet|kick|genou/i.test(t))?'hit':'';document.getElementById('drillLabel').textContent=t||'Démonstration'}
window.build=function(){let lev=$('level').value,n=+$('rounds').value,rs=+$('roundSeconds').value,rest=+$('restSeconds').value,out=warm.map(x=>({phase:x[0],title:x[1],detail:x[2],seconds:x[3]})),sets=drillSets[lev];for(let r=1;r<=n;r++){const d=sets[(r-1)%sets.length],cmd=[];while(cmd.length<Math.max(5,Math.floor(rs/16)))cmd.push(...d.commands.map(swap));out.push({phase:`Sac — round ${r}/${n}`,title:d.name,detail:d.focus,seconds:rs,commands:cmd.slice(0,Math.max(5,Math.floor(rs/16)))});if(r<n)out.push({phase:'Récupération',title:'Respire et analyse',detail:'Marche. Relâche les épaules. Prépare le thème suivant.',seconds:rest})}if($('conditioning').checked){out.push({phase:'Condition physique',title:'Squats contrôlés',detail:'Genoux dans l’axe, dos droit.',seconds:45});out.push({phase:'Condition physique',title:'Pompes ou pompes inclinées',detail:'Reste gainé, amplitude propre.',seconds:40});out.push({phase:'Condition physique',title:'Mountain climbers',detail:'Rythme régulier, bassin stable.',seconds:40})}cool.forEach(x=>out.push({phase:x[0],title:x[1],detail:x[2],seconds:x[3]}));return out};
const oldShow=window.showStep;window.showStep=function(){oldShow();if(idx<program.length)animate(program[idx].title)};
const oldTick=window.tick;window.tick=function(){if(paused)return;const before=document.getElementById('instruction').textContent;oldTick();const after=document.getElementById('instruction').textContent;if(before!==after)animate(after)};
})();