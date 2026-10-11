(function(){'use strict';
const $=id=>document.getElementById(id), status=$('readerStatus'), synth=window.speechSynthesis;
let book=[],rows=[],queue=[],index=0,repeat=0,token=0,paused=false,timer=null,active=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function voice(){return synth&&synth.getVoices().find(v=>/^ja[-_]/i.test(v.lang));}
function say(t,done){if(!synth||!window.SpeechSynthesisUtterance){status.textContent='此浏览器不支持语音朗读';return false;}synth.cancel();const u=new SpeechSynthesisUtterance(t);u.lang='ja-JP';u.rate=Number($('readerSpeed').value)||.85;const v=voice();if(v)u.voice=v;u.onend=()=>done&&done();u.onerror=e=>{if(e.error!=='canceled'&&e.error!=='interrupted')status.textContent='朗读失败：'+e.error;};synth.speak(u);return true;}
function stop(){token++;clearTimeout(timer);synth&&synth.cancel();paused=false;active=null;$('readerPause').textContent='暂停';}
window.ShiciSpeech={sayWord:(word,reading)=>{stop();say(reading||word);}};
document.addEventListener('click',e=>{const b=e.target.closest('button[data-speak]');if(b)window.ShiciSpeech.sayWord(b.dataset.speak,b.dataset.reading);});
function colName(i){let s='';for(i++;i;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s;return s;}
function render(){const sel=$('readerCol'),old=sel.value;sel.innerHTML=(rows[0]||[]).map((v,i)=>'<option value="'+i+'">'+colName(i)+' 列 · '+esc(String(v).slice(0,30))+'</option>').join('');sel.value=old&&+old<rows[0]?.length?old:'0';build();}
function build(){stop();const col=+$('readerCol').value,begin=$('readerHeader').checked?1:0;queue=rows.slice(begin).map((r,i)=>({text:String(r[col]??'').trim(),row:i+begin+1})).filter(x=>x.text);index=0;status.textContent='准备就绪：'+queue.length+' 个单元格';draw();}
function draw(){const list=$('readerPreview');list.innerHTML=queue.slice(Math.max(0,index-3),Math.min(queue.length,index+8)).map((q,i)=>{const n=Math.max(0,index-3)+i;return '<div class="reader-item '+(n===index?'current':'')+'"><span>'+q.row+'</span><strong lang="ja">'+esc(q.text)+'</strong><button type="button" data-reader-row="'+n+'" aria-label="从这行开始">▶</button></div>';}).join('');$('readerProgress').textContent=queue.length?(index+1)+' / '+queue.length:'0 / 0';}
function next(t){if(t!==token||paused)return;if(index>=queue.length){status.textContent='朗读完成';return;}active=queue[index];draw();status.textContent='正在朗读第 '+active.row+' 行：'+active.text;const ok=say(active.text,()=>{if(t!==token||paused)return;repeat++;if(repeat>=Number($('readerRepeat').value)){repeat=0;index++;}timer=setTimeout(()=>next(t),Number($('readerGap').value)*1000);});if(!ok)stop();}
function start(n){stop();index=n??0;repeat=0;const t=token;next(t);}
$('readerStart').addEventListener('click',()=>{if(!queue.length)return;start(index>=queue.length?0:index);});
$('readerStop').addEventListener('click',()=>{stop();status.textContent='已停止';});
$('readerPause').addEventListener('click',()=>{if(!queue.length)return;if(!paused){paused=true;clearTimeout(timer);synth&&synth.pause();$('readerPause').textContent='继续';status.textContent='已暂停';}else{paused=false;$('readerPause').textContent='暂停';if(synth&&synth.paused)synth.resume();else next(token);}});
$('readerCol').addEventListener('change',build);$('readerHeader').addEventListener('change',build);
$('readerPreview').addEventListener('click',e=>{const b=e.target.closest('[data-reader-row]');if(b)start(+b.dataset.readerRow);});
$('readerFile').addEventListener('change',async e=>{const f=e.target.files[0];if(!f)return;stop();try{if(!window.XLSX)throw Error('Excel 读取组件未加载，请刷新重试');const data=await f.arrayBuffer();const wb=XLSX.read(data,{type:'array',cellDates:false});book=wb.SheetNames.map(n=>({name:n,rows:XLSX.utils.sheet_to_json(wb.Sheets[n],{header:1,defval:'',blankrows:false})}));$('readerSheet').innerHTML=book.map((b,i)=>'<option value="'+i+'">'+esc(b.name)+'</option>').join('');rows=book[0].rows;render();status.textContent='已读取 '+esc(f.name)+' · '+rows.length+' 行';}catch(err){status.textContent='读取失败：'+err.message;}});
$('readerSheet').addEventListener('change',e=>{rows=book[+e.target.value]?.rows||[];render();});
})();