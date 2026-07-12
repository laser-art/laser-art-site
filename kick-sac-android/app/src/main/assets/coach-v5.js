(()=>{
const $=id=>document.getElementById(id);
const style=document.createElement('style');style.textContent=`
.videoCoach{margin:14px 0;padding:14px;border-radius:16px;background:#171717;border:1px solid #3a3a3a;text-align:left}.videoCoach h3{margin:0 0 8px;color:#f0b429}.videoBtn{width:100%;background:#e62117;color:#fff;border:0;border-radius:13px;padding:14px;font-weight:900;margin-top:10px}.videoSource{font-size:12px;color:#aaa;margin-top:8px}.videoHint{font-size:13px;color:#ddd;line-height:1.45}.videoTag{display:inline-block;background:#2b2517;color:#ffd675;padding:5px 9px;border-radius:999px;font-size:12px;font-weight:800}
`;
document.head.appendChild(style);
const card=document.querySelector('#workout .card');
const box=document.createElement('div');box.className='videoCoach';box.innerHTML=`<span class="videoTag">Démonstration réelle</span><h3 id="videoTitle">Vidéo de référence</h3><div id="videoHint" class="videoHint">Ouvre la démonstration avant de commencer le mouvement.</div><button id="videoBtn" class="videoBtn">Voir la vidéo professionnelle</button><div id="videoSource" class="videoSource">Source : chaîne officielle d’un entraîneur ou combattant reconnu.</div>`;
card.insertBefore(box,$('timer'));

const sources={
 warmup:{channel:'fightTIPS',query:'kickboxing warm up dynamic mobility'},
 rope:{channel:'fightTIPS',query:'jump rope boxing warm up'},
 shoulders:{channel:'fightTIPS',query:'boxing shoulder warm up mobility'},
 hips:{channel:'fightTIPS',query:'kickboxing hip mobility warm up'},
 legswings:{channel:'fightTIPS',query:'kickboxing leg swings warm up'},
 stance:{channel:'Gabriel Varga',query:'kickboxing stance footwork tutorial'},
 shadow:{channel:'Gabriel Varga',query:'kickboxing shadow boxing tutorial'},
 jab:{channel:'Gabriel Varga',query:'kickboxing jab tutorial'},
 cross:{channel:'Gabriel Varga',query:'kickboxing cross straight right tutorial'},
 hook:{channel:'Gabriel Varga',query:'kickboxing hook tutorial'},
 uppercut:{channel:'Gabriel Varga',query:'kickboxing uppercut tutorial'},
 lowkick:{channel:'Gabriel Varga',query:'kickboxing low kick tutorial'},
 middlekick:{channel:'fightTIPS',query:'kickboxing roundhouse body kick tutorial'},
 frontkick:{channel:'Wonderboy Thompson',query:'front kick tutorial'},
 knee:{channel:'Gabriel Varga',query:'kickboxing knee strike tutorial'},
 defense:{channel:'Gabriel Varga',query:'kickboxing defense slips blocks counters'},
 footwork:{channel:'Gabriel Varga',query:'kickboxing footwork angles tutorial'},
 bag:{channel:'Gabriel Varga',query:'heavy bag kickboxing workout technique'},
 cardio:{channel:'fightTIPS',query:'kickboxing cardio heavy bag workout'},
 squat:{channel:'Squat University',query:'bodyweight squat technique'},
 pushup:{channel:'ATHLEAN-X',query:'push up proper form'},
 mountain:{channel:'ATHLEAN-X',query:'mountain climber proper form'},
 stretch:{channel:'fightTIPS',query:'kickboxing cooldown stretching'}
};
function kind(text){text=(text||'').toLowerCase();if(/corde/.test(text))return'rope';if(/épaule|omoplate|bras/.test(text))return'shoulders';if(/hanche|bassin/.test(text))return'hips';if(/balancier|ouverture de hanche/.test(text))return'legswings';if(/garde/.test(text)&&/appui|déplacement|avance|recule/.test(text))return'stance';if(/shadow/.test(text))return'shadow';if(/low kick/.test(text))return'lowkick';if(/middle kick|kick au corps/.test(text))return'middlekick';if(/front kick/.test(text))return'frontkick';if(/genou/.test(text))return'knee';if(/crochet/.test(text))return'hook';if(/uppercut/.test(text))return'uppercut';if(/jab/.test(text)&&/direct/.test(text))return'cross';if(/jab/.test(text))return'jab';if(/esquive|blocage|parade|contre/.test(text))return'defense';if(/angle|pivot|sortie|déplacement/.test(text))return'footwork';if(/squat/.test(text))return'squat';if(/pompe/.test(text))return'pushup';if(/mountain/.test(text))return'mountain';if(/étirement|retour au calme|mobilité légère/.test(text))return'stretch';if(/cardio|sprint|intervalles/.test(text))return'cardio';if(/sac|poings|kick/.test(text))return'bag';return'warmup'}
function urlFor(s){const q=encodeURIComponent(`${s.channel} ${s.query}`);return `https://www.youtube.com/results?search_query=${q}`}
function updateVideo(text){const s=sources[kind(text)];$('videoTitle').textContent=text||'Vidéo de référence';$('videoHint').textContent=`Regarde d’abord la démonstration réelle correspondant à : ${text}. Mets la séance en pause pendant la vidéo.`;$('videoSource').textContent=`Source ciblée : ${s.channel} — recherche officielle YouTube.`;$('videoBtn').onclick=()=>{if(!paused)togglePause();try{Android.openVideo(urlFor(s))}catch(e){location.href=urlFor(s)}}}
const oldShow=window.showStep;window.showStep=function(){oldShow();if(idx<program.length){const s=program[idx];const text=s.segments?s.segments[0][0]:s.title;updateVideo(text)}};
const oldTick=window.tick;window.tick=function(){const before=$('instruction').textContent;oldTick();const after=$('instruction').textContent;if(before!==after)updateVideo(after)};
})();