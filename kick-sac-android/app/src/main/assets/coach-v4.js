(()=>{
const $=id=>document.getElementById(id);
const style=document.createElement('style');style.textContent=`
.coach-panel{margin:14px 0;padding:14px;border-radius:16px;background:#202020;border:1px solid #393939;text-align:left}.coach-panel h3{margin:0 0 6px;color:#f0b429}.coach-panel .line{padding:8px 0;border-top:1px solid #333}.coach-panel .line:first-of-type{border-top:0}.side-badge{display:inline-block;padding:5px 9px;border-radius:999px;background:#f0b429;color:#111;font-weight:900;font-size:12px}.intensity{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin-top:10px}.intensity span{padding:7px 2px;text-align:center;border-radius:8px;background:#292929;font-size:11px}.intensity span.on{background:#f0b429;color:#111;font-weight:900}.note{font-size:12px;color:#bbb;line-height:1.4}.exercise-map{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.exercise-map div{padding:9px;border-radius:10px;background:#292929;font-size:12px}.section-title{margin-top:18px;font-weight:900;color:#f0b429}
`;
document.head.appendChild(style);

const builder=$('builder').querySelector('.card');
const options=document.createElement('div');
options.innerHTML=`
<label>Discipline<select id="ruleset"><option value="k1">K-1 : poings, kicks, genoux, sans coudes</option><option value="lowkick">Low kick : poings et kicks, sans genoux</option><option value="fullcontact">Full contact : poings et kicks au-dessus de la taille</option></select></label>
<label>Type de séance<select id="sessionType"><option value="technique">Technique au sac</option><option value="cardio">Cardio combattant</option><option value="power">Puissance contrôlée</option><option value="fight">Simulation de combat</option></select></label>
<label>Préparation physique<select id="conditioningPlan"><option value="intervals">Intervalles spécifiques au sac</option><option value="bodyweight">Circuit poids du corps</option><option value="none">Aucun bloc supplémentaire</option></select></label>`;
builder.insertBefore(options,builder.querySelector('.primary'));

const card=document.querySelector('#workout .card');
const panel=document.createElement('div');panel.className='coach-panel';panel.innerHTML=`<h3 id="coachTitle">Consigne</h3><div class="line"><span id="sideBadge" class="side-badge">Deux côtés</span></div><div id="coachDetail" class="line">Travaille proprement et reviens en garde.</div><div id="coachPoints" class="exercise-map"></div><div class="intensity" id="intensity"><span>1–2</span><span>3–4</span><span>5–6</span><span>7–8</span><span>9–10</span></div><div class="note">Les consignes de l’application complètent le travail en club. Une correction technique par un entraîneur reste indispensable.</div>`;
card.insertBefore(panel,$('stepBar').parentElement);

const warmup=[
 {phase:'Échauffement général',title:'Corde à sauter ou pas légers',detail:'Monter progressivement la température sans fatigue.',segments:[['Rythme facile',60,'Deux pieds',3],['Pas alternés',60,'Deux pieds',4]]},
 {phase:'Mobilité dynamique',title:'Épaules et omoplates',detail:'Même travail des deux côtés.',segments:[['Cercles des deux épaules vers l’avant',20,'Deux côtés',3],['Change. Cercles des deux épaules vers l’arrière',20,'Deux côtés',3],['Bras tendus : petits cercles vers l’avant',20,'Deux côtés',3],['Change. Petits cercles vers l’arrière',20,'Deux côtés',3]]},
 {phase:'Mobilité dynamique',title:'Tronc et hanches',detail:'Amplitude progressive, bassin stable.',segments:[['Rotations du tronc à gauche et à droite',40,'Deux côtés',3],['Cercles de bassin vers la gauche',20,'Gauche',3],['Change. Cercles de bassin vers la droite',20,'Droite',3]]},
 {phase:'Mobilité dynamique',title:'Hanches et jambes',detail:'Travail identique jambe gauche et jambe droite.',segments:[['Ouverture de hanche jambe gauche',25,'Gauche',3],['Change. Ouverture de hanche jambe droite',25,'Droite',3],['Balanciers avant-arrière jambe gauche',25,'Gauche',4],['Change. Balanciers avant-arrière jambe droite',25,'Droite',4],['Balanciers latéraux jambe gauche',25,'Gauche',4],['Change. Balanciers latéraux jambe droite',25,'Droite',4]]},
 {phase:'Activation',title:'Appuis de kick-boxing',detail:'Reste en garde, petits déplacements, pas croisés interdits.',segments:[['Avance et recule en garde',30,'Deux côtés',4],['Déplacement latéral gauche et droite',30,'Deux côtés',4],['Pivots courts autour du sac',30,'Deux côtés',5]]},
 {phase:'Échauffement spécifique',title:'Shadow kick-boxing',detail:'50 à 60 % d’intensité, aucune frappe lourde.',segments:[['Jab et direct en déplacement',30,'Garde choisie',5],['Jab, direct, crochet, sortie d’angle',30,'Garde choisie',5],['Kicks légers alternés, retour en garde',30,'Gauche et droite',5],['Combinaisons libres légères',30,'Deux côtés',5]]},
 {phase:'Mise en route au sac',title:'Contact progressif avec le sac',detail:'Augmente doucement l’impact avant les rounds.',segments:[['Poings à 40 %',30,'Deux mains',4],['Kicks à 40 %, gauche puis droite',30,'Gauche et droite',4],['Poings et kicks à 60 %',30,'Deux côtés',5]]}
];

const techniqueRounds={
 k1:[
  {title:'Fondamentaux poings',rpe:5,cues:['Jab précis','Jab, direct','Double jab, direct','Jab au corps, direct à la tête'],points:['Menton protégé','Retour immédiat en garde','Appuis stables','Respire sur chaque frappe']},
  {title:'Poings vers low kick',rpe:6,cues:['Jab, direct, low kick arrière','Jab, crochet avant, low kick arrière','Direct, crochet avant, low kick avant'],points:['Le kick termine la série','Pivote le pied d’appui','Reviens stable','Garde haute']},
  {title:'Genoux courts au sac',rpe:6,cues:['Jab, direct, genou arrière','Crochet avant, genou arrière','Deux genoux alternés','Direct, genou, sortie'],points:['Bassin vers l’avant','Retour en garde','Pas de traction violente du sac','Travail des deux genoux']},
  {title:'Défense et contre',rpe:6,cues:['Esquive extérieure, direct, crochet','Blocage imaginaire, direct, low kick','Pas arrière, direct, genou','Parade imaginaire, jab, direct'],points:['Défense avant la riposte','Tête hors de l’axe','Réponse courte','Sortie après la série']},
  {title:'Angles et sorties',rpe:6,cues:['Jab, direct, pas à gauche','Double jab, sortie à droite','Direct, crochet, pivot, low kick','Jab, angle, direct'],points:['Ne croise pas les pieds','Regarde le sac','Petit pivot','Reprends la distance']}
 ],
 lowkick:[
  {title:'Fondamentaux poings',rpe:5,cues:['Jab précis','Jab, direct','Double jab, direct','Jab au corps, direct à la tête'],points:['Menton protégé','Retour en garde','Appuis stables','Respire']},
  {title:'Combinaisons low kick',rpe:6,cues:['Jab, direct, low kick arrière','Crochet avant, low kick arrière','Direct, crochet, low kick avant','Double jab, direct, low kick'],points:['Travail gauche et droite','Pivote le pied d’appui','Garde haute','Reviens stable']},
  {title:'Défense et contre',rpe:6,cues:['Blocage low kick imaginaire, direct','Esquive, crochet, low kick','Pas arrière, direct, crochet','Parade, jab, direct'],points:['Défense avant riposte','Ne reste pas dans l’axe','Réponse courte','Sortie latérale']},
  {title:'Angles et volume',rpe:6,cues:['Jab, direct, angle','Crochet, direct, sortie','Trois poings, low kick','Double jab en avançant, recule'],points:['Appuis actifs','Pas croisés interdits','Rythme régulier','Technique propre']}
 ],
 fullcontact:[
  {title:'Fondamentaux poings',rpe:5,cues:['Jab précis','Jab, direct','Double jab, direct','Jab au corps, direct à la tête'],points:['Menton protégé','Retour en garde','Appuis stables','Respire']},
  {title:'Kicks au corps et à la tête',rpe:6,cues:['Jab, direct, middle kick arrière','Jab, crochet, front kick','Direct, middle kick avant','Double jab, high kick contrôlé'],points:['Aucun low kick','Amplitude contrôlée','Travail des deux jambes','Retour en garde']},
  {title:'Défense et contre',rpe:6,cues:['Esquive, direct, crochet','Pas arrière, direct, middle kick','Parade, jab, direct','Blocage imaginaire, crochet, front kick'],points:['Défense avant riposte','Tête hors de l’axe','Sortie latérale','Distance correcte']}
 ]
};

const cardioRounds=[
 {title:'Volume technique continu',rpe:7,cues:['Jab-direct en continu','Crochets alternés','Poings et kicks en continu','Déplacement actif autour du sac'],points:['Ne bloque pas la respiration','Impact modéré','Cadence régulière','Technique avant vitesse']},
 {title:'Intervalles 15/15',rpe:8,segments:[['15 secondes très rapides : poings droits',15,'Deux mains',9],['15 secondes actives : déplacement et jab',15,'Deux côtés',4],['15 secondes très rapides : crochets',15,'Deux mains',9],['15 secondes actives : déplacement et jab',15,'Deux côtés',4],['15 secondes très rapides : kicks alternés',15,'Gauche et droite',9],['15 secondes actives : déplacement',15,'Deux côtés',4]],points:['Explosif pendant le travail','Récupération active','Garde haute','Reste propre']},
 {title:'Round à accélérations',rpe:8,cues:['Rythme combat','Accélère 10 secondes','Reviens au rythme combat','Accélère 10 secondes'],points:['Ne pars pas à fond trop tôt','Respire','Récupère en bougeant','Finis le round fort']},
 {title:'Corps entier',rpe:8,cues:['Jab, direct, kick','Crochet, crochet, kick','Poings, genou si autorisé','Front kick, direct, crochet'],points:['Alterner haut et bas','Reste équilibré','Impact modéré','Cadence élevée']}
];

const powerRounds=[
 {title:'Puissance des poings',rpe:7,cues:['Jab léger, direct puissant','Direct, crochet puissant','Jab au corps, direct à la tête','Crochet avant, crochet arrière'],points:['70 à 80 % maximum','Puissance depuis les appuis','Pas de crispation','Reviens en garde']},
 {title:'Puissance des kicks',rpe:7,cues:['Jab, direct, kick arrière puissant','Crochet, kick arrière','Direct, kick avant','Kick seul, replacement'],points:['Pivote le pied d’appui','Traverse la cible','Ne perds pas l’équilibre','Travaille les deux jambes']},
 {title:'Puissance en combinaison',rpe:8,cues:['Jab, direct, crochet, kick','Double jab, direct, kick','Direct, crochet, kick, sortie','Jab, kick, direct'],points:['Une frappe forte par série','Les autres préparent','Repos actif','Technique stricte']}
];

const fightRounds=[
 {title:'Pression contrôlée',rpe:7,cues:['Double jab en avançant, direct','Jab, crochet, direct, kick','Trois frappes, angle, deux frappes','Jab, direct, sortie, reprise'],points:['Avance sans te jeter','Coupe la sortie imaginaire','Reste en garde','Ne pousse pas le sac']},
 {title:'Contre-attaque',rpe:7,cues:['Esquive, direct, crochet','Pas arrière, direct, kick','Blocage imaginaire, direct, crochet','Parade, jab, direct, sortie'],points:['Fais manquer avant de répondre','Réponse courte','Tête hors de l’axe','Reprends la distance']},
 {title:'Changement de rythme',rpe:8,cues:['Jab lent, direct rapide','Double jab léger, direct puissant','Feinte, crochet, kick','Rythme calme, puis rafale'],points:['Ne sois pas prévisible','Relâché entre les rafales','Garde haute','Reste équilibré']},
 {title:'Simulation de round',rpe:9,cues:['Pression 20 secondes','Défense et contre','Déplacement actif','Rafale finale'],points:['Gère ton énergie','Imagine un adversaire','Varie les niveaux','Finis fort sans perdre la forme']}
];

const conditioning={
 intervals:[
  {phase:'Cardio spécifique',title:'Sprints au sac',detail:'Efforts courts répétés avec récupération active.',segments:[['20 secondes poings très rapides',20,'Deux mains',9],['20 secondes déplacement actif',20,'Deux côtés',4],['20 secondes kicks alternés rapides',20,'Gauche et droite',9],['20 secondes déplacement actif',20,'Deux côtés',4],['20 secondes combinaison libre rapide',20,'Deux côtés',9],['40 secondes récupération active',40,'Deux côtés',3]]}
 ],
 bodyweight:[
  {phase:'Préparation physique',title:'Circuit combattant',detail:'Qualité de mouvement malgré la fatigue.',segments:[['Squats contrôlés',30,'Deux jambes',7],['Récupération debout',20,'Deux côtés',3],['Mountain climbers',30,'Deux côtés',8],['Récupération debout',20,'Deux côtés',3],['Pompes ou pompes inclinées',30,'Deux bras',7],['Montées de genoux',30,'Deux côtés',8]]}
 ]
};

const cooldown=[
 {phase:'Retour au calme',title:'Marche et respiration',detail:'Faire redescendre progressivement le rythme.',segments:[['Marche lente',45,'Deux côtés',2],['Respiration lente : expiration plus longue',45,'Deux côtés',2]]},
 {phase:'Mobilité légère',title:'Relâchement symétrique',detail:'Pas d’étirement forcé.',segments:[['Épaules et bras, côté gauche',25,'Gauche',2],['Change. Épaules et bras, côté droit',25,'Droite',2],['Hanche et quadriceps, jambe gauche',25,'Gauche',2],['Change. Hanche et quadriceps, jambe droite',25,'Droite',2],['Mollet gauche',20,'Gauche',2],['Change. Mollet droit',20,'Droite',2]]}
];

function expand(x){return {...x,seconds:x.segments.reduce((a,s)=>a+s[1],0),segIndex:0}}
function allowedCue(c,rules){if(rules==='lowkick'&&/genou/i.test(c))return c.replace(/,? ?genou[^,]*/gi,'');if(rules==='fullcontact'&&/low kick/i.test(c))return c.replace(/low kick/gi,'middle kick');return c}
window.build=function(){const rules=$('ruleset').value,type=$('sessionType').value,n=+$('rounds').value,rs=+$('roundSeconds').value,rest=+$('restSeconds').value;let out=warmup.map(expand);let pool=type==='technique'?techniqueRounds[rules]:type==='cardio'?cardioRounds:type==='power'?powerRounds:fightRounds;for(let r=1;r<=n;r++){const d=pool[(r-1)%pool.length];if(d.segments){let reps=[],total=0;while(total<rs){for(const s of d.segments){reps.push([allowedCue(s[0],rules),s[1],s[2],s[3]]);total+=s[1];if(total>=rs)break}}out.push({phase:`Sac — round ${r}/${n}`,title:d.title,detail:'Round structuré avec changements annoncés.',segments:reps,seconds:reps.reduce((a,s)=>a+s[1],0),points:d.points,rpe:d.rpe,segIndex:0})}else{let cues=[];while(cues.length<Math.max(6,Math.floor(rs/15)))cues.push(...d.cues.map(c=>allowedCue(c,rules)).filter(Boolean));out.push({phase:`Sac — round ${r}/${n}`,title:d.title,detail:'Exécute la consigne puis replace-toi en garde.',commands:cues.slice(0,Math.max(6,Math.floor(rs/15))),seconds:rs,points:d.points,rpe:d.rpe})}if(r<n)out.push({phase:'Récupération',title:'Récupération active',detail:'Marche, respire, relâche les épaules et prépare le round suivant.',seconds:rest,rpe:2,points:['Ne t’assieds pas','Respiration calme','Analyse le round','Prépare la prochaine consigne']})}const c=$('conditioningPlan').value;if(c!=='none')out.push(...conditioning[c].map(expand));out.push(...cooldown.map(expand));return out};

function setIntensity(v){document.querySelectorAll('#intensity span').forEach((e,i)=>e.classList.toggle('on',v>=i*2+1&&v<=i*2+2))}
function setPanel(s,label){$('coachTitle').textContent=s.title;$('sideBadge').textContent=label||'Deux côtés';$('coachDetail').textContent=s.detail||'';$('coachPoints').innerHTML=(s.points||['Technique propre','Respiration','Retour en garde','Appuis stables']).map(x=>`<div>${x}</div>`).join('');setIntensity(s.rpe||5)}
window.showStep=function(){if(idx>=program.length)return finish();const s=program[idx];left=s.seconds;s.cmd=0;s.interval=s.commands?Math.max(8,Math.floor(s.seconds/s.commands.length)):0;s.segIndex=0;$('phase').textContent=s.phase;$('stepCount').textContent=`${idx+1}/${program.length}`;const label=s.segments?s.segments[0][0]:s.title;$('instruction').textContent=label;$('detail').textContent=s.detail;$('timer').textContent=fmt(left);$('stepBar').style.width='0%';setPanel(s,s.segments?s.segments[0][2]:'Deux côtés');speak(`${s.phase}. ${s.title}. ${label}. ${s.detail}`);buzz()};
window.tick=function(){if(paused)return;const s=program[idx];left--;const elapsed=s.seconds-left;if(s.segments){let acc=0,newI=0;for(let i=0;i<s.segments.length;i++){acc+=s.segments[i][1];if(elapsed<acc){newI=i;break}}if(newI!==s.segIndex){s.segIndex=newI;const seg=s.segments[newI];$('instruction').textContent=seg[0];$('sideBadge').textContent=seg[2];setIntensity(seg[3]);speak(`Change. ${seg[0]}`);buzz(90)}}else if(s.commands&&left>0&&elapsed>0&&elapsed%s.interval===0&&s.cmd<s.commands.length){const c=s.commands[s.cmd++];$('instruction').textContent=c;speak(c)}$('timer').textContent=fmt(left);$('stepBar').style.width=Math.min(100,(s.seconds-left)/s.seconds*100)+'%';if(left===20&&s.phase.startsWith('Sac'))speak('Vingt secondes. Garde la technique et termine le round proprement.');if(left<=0){buzz(220);idx++;showStep()}};

const oldHome=window.renderHome;window.renderHome=function(){oldHome();const text=document.querySelector('#home .card:first-child .muted');if(text)text.textContent='Kick Sac V4 : échauffement dynamique symétrique, rounds spécifiques au kick-boxing, cardio combattant, puissance et simulation de combat. Les animations approximatives ont été supprimées pour éviter des démonstrations trompeuses.'};
})();