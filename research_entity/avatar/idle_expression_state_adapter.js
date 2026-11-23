/* Maps existing FranKenstein buehne/status signals into idle-expression drives.
 * No synthetic mood model: all deviations from baseline are tied to fields
 * already emitted by buehne_daemon.py or to the existing self-emote category.
 */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.FrankensteinIdleState=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const c=v=>Math.max(0,Math.min(1,Number.isFinite(+v)?+v:0));
  const EXPRESSIONS={
    '01_ruhig_neutral':{},
    '02_wach_aufmerksam':{arousal:.62,curiosity:.82,attention:.92,fatigue:.08},
    '03_angespannt':{valence:.26,arousal:.78,tension:.90,uncertainty:.58,attention:.86},
    '04_zugewandt_weich':{valence:.84,arousal:.38,tension:.10,presence:.78,attention:.72},
    '05_erschoepft_schwer':{valence:.40,arousal:.16,tension:.28,fatigue:.92,attention:.38},
    '06_ueberrascht':{valence:.52,arousal:.94,tension:.44,curiosity:.90,uncertainty:.72,attention:.96}
  };
  const SELF={
    self_creative:{playfulness:.90,curiosity:.88,valence:.72,arousal:.62},
    self_confident:{valence:.72,tension:.10,uncertainty:.08,attention:.78},
    self_uncertain:{valence:.43,tension:.56,uncertainty:.92,attention:.84},
    self_empathetic:{valence:.80,tension:.08,presence:.88,attention:.80},
    self_technical:{playfulness:.08,curiosity:.66,attention:.94,arousal:.48},
    self_neutral:{}
  };
  function maxInto(dst,src,weight=1){for(const [k,v] of Object.entries(src||{}))dst[k]=Math.max(dst[k]||0,c(v*weight));return dst;}
  function mix(a,b,w){return c(a*(1-w)+b*w);}
  function fromBuehneStatus(status,ctx){
    status=status||{};ctx=ctx||{};const b=status.buehne||status;
    const s={valence:.52,arousal:.30,tension:.16,fatigue:.12,curiosity:.38,playfulness:.12,uncertainty:.18,presence:.28,attention:.48,speaking:!!ctx.speaking,listening:!!ctx.listening,engaged:status.an!==false};
    maxInto(s,EXPRESSIONS[b.ausdruck]||{});
    if(Number.isFinite(+b.broadcast_value))s.arousal=Math.max(s.arousal,c(+b.broadcast_value/3));
    if(Number.isFinite(+b.ueberraschung)){
      const u=c(+b.ueberraschung);s.arousal=Math.max(s.arousal,.25+.70*u);s.curiosity=Math.max(s.curiosity,.30+.60*u);s.uncertainty=Math.max(s.uncertainty,.15+.45*u);
    }
    const look=b.blick||{};
    if(look.anwesend){s.presence=Math.max(s.presence,look.nah?.90:.68);s.attention=Math.max(s.attention,.82);}
    if(Number.isFinite(+b.swap_voll_anteil)){
      const p=c((+b.swap_voll_anteil-.72)/.28);s.tension=Math.max(s.tension,.15+.72*p);s.fatigue=Math.max(s.fatigue,.12+.42*p);
    }
    if(Number.isFinite(+b.ram_frei_anteil)){
      const p=c((.22-(+b.ram_frei_anteil))/.22);s.tension=Math.max(s.tension,.15+.62*p);s.fatigue=Math.max(s.fatigue,.12+.34*p);
    }
    const age=Number.isFinite(+ctx.selfCategoryAgeMs)?Math.max(0,+ctx.selfCategoryAgeMs):Infinity;
    if(ctx.selfCategory&&SELF[ctx.selfCategory]&&age<90000){
      const w=age<15000?1:Math.max(0,1-(age-15000)/75000);
      const d=SELF[ctx.selfCategory];
      for(const [k,v] of Object.entries(d))s[k]=mix(s[k],Math.max(s[k],v),w);
    }
    if(s.speaking){s.playfulness*=.35;s.curiosity*=.7;}
    return s;
  }
  return {fromBuehneStatus,EXPRESSIONS,SELF};
});
