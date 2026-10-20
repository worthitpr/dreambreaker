# Copyright 2026 Kritsia Quiñones (XXSELENEPRXX). Licensed under the Apache License, Version 2.0.
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Iterable
import hashlib, json, math, re, statistics
from datetime import date

SEARCH_LAYERS = [
    'exact_phrase','synonyms','problem_language','mechanism_language','claim_language',
    'adjacent_categories','direct_products','platform_features','company_portfolios',
    'open_source','patents_domestic','patents_foreign_pct','patent_families',
    'classification_codes','citations_backward','citations_forward','nonpatent_literature',
    'standards','historical_attempts','failed_products','workarounds','multilingual',
    'acquisitions_shutdowns','regulatory_sources'
]

KILL_DIMENSIONS = [
    'problem_reality','frequency_severity','buyer_payer','direct_competition','substitutes',
    'prior_art','platform_absorption','technical_feasibility','technology_readiness',
    'security_privacy','regulatory','onboarding_friction','unit_economics','distribution',
    'switching_cost','defensibility','data_advantage','ai_commoditization','timing',
    'operational_burden','dependency_fragility','copyability','evidence_quality','market_proof'
]

CRITICAL_SOURCE_TYPES={'patent','official_product','standard','regulator','peer_reviewed','source_code','official_registry'}

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_type: str
    title: str
    url_or_ref: str
    date: str
    claim: str
    similarity: float
    independence_group: str
    directness: str='INDIRECT'
    freshness: str='CURRENT'
    supports: str='EXISTS_OR_OVERLAPS'
    family_id: str|None=None
    entity_id: str|None=None
    mechanism_id: str|None=None
    jurisdiction: str|None=None
    legal_status: str|None=None
    claim_coverage: float=0.0

class Dreambreaker:
    """Deterministic reference core for adversarial idea evaluation.

    It does not perform web search itself. It plans/searches/classifies evidence supplied by an
    authorized research layer and enforces fail-closed novelty discipline.
    """

    def fingerprint(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        required=['name','problem','user','mechanism','outcome']
        missing=[k for k in required if not str(idea.get(k,'')).strip()]
        assumptions=list(idea.get('assumptions',[]))
        differentiators=list(idea.get('differentiators',[]))
        dependencies=list(idea.get('dependencies',[]))
        return {
            'idea_name': idea.get('name','UNNAMED'),
            'missing': missing,
            'claims': [x for x in [idea.get('problem'),idea.get('mechanism'),idea.get('outcome')] if x],
            'assumptions': assumptions,
            'buyer': idea.get('buyer'),
            'constraints': list(idea.get('constraints',[])),
            'differentiators': differentiators,
            'dependencies': dependencies,
            'jurisdictions': list(idea.get('jurisdictions',[])),
        }

    def claim_atoms(self, idea: Dict[str,Any]) -> List[Dict[str,str]]:
        atoms=[]
        mapping=[('problem',idea.get('problem')),('user',idea.get('user')),('buyer',idea.get('buyer')),
                 ('mechanism',idea.get('mechanism')),('outcome',idea.get('outcome'))]
        for typ,val in mapping:
            if val: atoms.append({'type':typ,'text':str(val)})
        for d in idea.get('differentiators',[]): atoms.append({'type':'differentiator','text':str(d)})
        for a in idea.get('assumptions',[]): atoms.append({'type':'assumption','text':str(a)})
        return atoms

    def query_lattice(self, idea: Dict[str, Any]) -> List[Dict[str,str]]:
        base=' '.join(str(x) for x in [idea.get('name',''), idea.get('problem',''), idea.get('mechanism',''), idea.get('outcome','')] if x)
        tokens=[t for t in re.findall(r"[A-Za-z0-9_-]+", base.lower()) if len(t)>2]
        seen=[]
        for t in tokens:
            if t not in seen: seen.append(t)
        core=' '.join(seen[:12]) or 'unknown idea'
        qs=[]
        suffixes={
            'exact_phrase':'"'+str(idea.get('name',''))+'"',
            'claim_language':'claims apparatus method system workflow',
            'patents_domestic':'USPTO patent application prior art claims',
            'patents_foreign_pct':'PCT WIPO EPO foreign patent',
            'patent_families':'patent family priority continuations equivalents',
            'nonpatent_literature':'paper research benchmark thesis proceedings',
            'open_source':'github gitlab open source repository',
            'platform_features':'Microsoft Google AWS OpenAI Apple Salesforce ServiceNow feature',
            'company_portfolios':'company product portfolio acquisition subsidiary',
            'failed_products':'shutdown discontinued failed startup postmortem',
            'historical_attempts':'history previous attempt archived legacy',
            'workarounds':'workaround spreadsheet manual process forum reddit',
            'multilingual':'Spanish German French Portuguese Japanese Chinese Korean equivalents',
            'classification_codes':'CPC IPC classification technical class',
            'citations_backward':'references cited prior art',
            'citations_forward':'cited by successor patents papers',
            'acquisitions_shutdowns':'acquired sunset discontinued merged',
            'regulatory_sources':'regulator law rule standard compliance',
        }
        for layer in SEARCH_LAYERS:
            suffix=suffixes.get(layer,layer.replace('_',' '))
            qs.append({'layer':layer,'query':(core+' '+suffix).strip()})
        return qs

    def normalize_evidence(self, evidence: Iterable[Evidence]) -> List[Evidence]:
        """Deduplicate obvious repeats, especially patent-family duplicates.
        Keeps the most direct/high-similarity member of each family/entity."""
        buckets={}
        for e in evidence:
            if e.source_type=='patent' and e.family_id:
                key=('patent_family',e.family_id)
            elif e.entity_id:
                key=('entity',e.entity_id)
            else:
                key=('evidence',e.evidence_id)
            cur=buckets.get(key)
            if cur is None or (e.directness=='DIRECT',e.similarity,e.claim_coverage) > (cur.directness=='DIRECT',cur.similarity,cur.claim_coverage):
                buckets[key]=e
        return list(buckets.values())

    def evidence_health(self, evidence: List[Evidence]) -> Dict[str,Any]:
        raw=len(evidence)
        ev=self.normalize_evidence(evidence)
        if not ev:
            return {'raw_count':raw,'dedup_count':0,'independent_groups':0,'critical_sources':0,'source_types':0,
                    'max_similarity':0.0,'coverage':'NONE','patent_family_duplicates':0,'source_concentration':1.0}
        groups=[e.independence_group for e in ev]
        independent=len(set(groups))
        critical=sum(1 for e in ev if e.source_type in CRITICAL_SOURCE_TYPES)
        source_types=len({e.source_type for e in ev})
        mx=max(e.similarity for e in ev)
        family_dupes=raw-len(ev)
        top_group=max(groups.count(g) for g in set(groups))
        concentration=round(top_group/len(ev),3)
        cov='HIGH' if len(ev)>=8 and independent>=4 and critical>=2 and source_types>=3 and concentration<=0.5 else 'MEDIUM' if len(ev)>=4 and independent>=2 else 'LOW'
        return {'raw_count':raw,'dedup_count':len(ev),'independent_groups':independent,'critical_sources':critical,
                'source_types':source_types,'max_similarity':round(mx,3),'coverage':cov,
                'patent_family_duplicates':family_dupes,'source_concentration':concentration}

    def search_coverage(self, searched_layers: List[str], required_layers: List[str]|None=None) -> Dict[str,Any]:
        required=required_layers or SEARCH_LAYERS
        got=set(searched_layers); req=set(required)
        covered=len(req & got); total=len(req)
        ratio=covered/total if total else 1.0
        missing=sorted(req-got)
        return {'covered':covered,'total':total,'ratio':round(ratio,4),'missing':missing,'complete':not missing}

    def existence_classification(self, evidence: List[Evidence], searched_layers: List[str], material_delta_score:float=0.0, material_delta_independent_evidence:int=0) -> Dict[str,Any]:
        ev=self.normalize_evidence(evidence)
        health=self.evidence_health(evidence)
        coverage=self.search_coverage(searched_layers)
        direct=[e for e in ev if e.similarity>=0.90 and e.directness=='DIRECT' and e.claim_coverage>=0.65]
        same_mech=[e for e in ev if e.similarity>=0.78 and (e.mechanism_id is not None or e.claim_coverage>=0.65)]
        close=[e for e in ev if e.similarity>=0.75]
        mech=[e for e in ev if 0.50<=e.similarity<0.75]
        if direct and material_delta_score < 0.65:
            status='EXISTS_CLOSE_OR_SAME'
        elif direct and material_delta_score >= 0.65 and material_delta_independent_evidence>=2:
            status='EXISTS_CLOSE_BUT_MATERIAL_DELTA_SUPPORTED'
        elif direct and material_delta_score >= 0.65:
            status='EXISTS_CLOSE_DELTA_UNVERIFIED'
        elif same_mech:
            status='SAME_MECHANISM_DIFFERENT_PACKAGING'
        elif len(close)>=2:
            status='STRONG_OVERLAP'
        elif mech:
            status='MECHANISM_PRIOR_ART'
        elif coverage['complete']:
            status='NO_CLOSE_MATCH_FOUND_IN_SEARCH_SCOPE'
        else:
            status='UNKNOWN_INSUFFICIENT_SEARCH'
        return {
            'status':status,
            'direct_matches':[e.evidence_id for e in direct],
            'same_mechanism_matches':[e.evidence_id for e in same_mech],
            'close_matches':[e.evidence_id for e in close],
            'mechanism_matches':[e.evidence_id for e in mech],
            'search_saturated':coverage['complete'],
            'search_coverage':coverage,
            'health':health,
            'material_delta_score':round(float(material_delta_score),3),
            'novelty_status':'NOVELTY_NOT_PROVEN'
        }



    def search_execution_gate(self, receipts:List[Dict[str,Any]], required_layers:List[str]|None=None) -> Dict[str,Any]:
        required=required_layers or SEARCH_LAYERS
        by_layer={}
        for r in receipts:
            if r.get('executed') is True and r.get('layer'):
                by_layer.setdefault(r['layer'],[]).append(r)
        missing=[layer for layer in required if layer not in by_layer]
        failed=[layer for layer,rs in by_layer.items() if all(r.get('error') for r in rs)]
        zero_hits=[layer for layer,rs in by_layer.items() if any((r.get('error') in (None,'') and int(r.get('result_count',0))==0) for r in rs)]
        return {'pass':not missing and not failed,'missing_layers':missing,'failed_layers':failed,'zero_hit_layers':sorted(zero_hits),'executed_layers':len(by_layer),'required_layers':len(required)}

    def zero_hit_is_evidence(self, receipt:Dict[str,Any]) -> bool:
        return bool(receipt.get('executed') is True and not receipt.get('error') and int(receipt.get('result_count',-1))==0 and receipt.get('query') and receipt.get('timestamp') and receipt.get('tool'))

    def research_reproducibility(self, receipts:List[Dict[str,Any]]) -> Dict[str,Any]:
        valid=[r for r in receipts if r.get('executed') is True and r.get('query') and r.get('timestamp') and r.get('tool') and r.get('layer')]
        queries=[r.get('query') for r in valid]
        unique=len(set(queries))
        ratio=unique/len(queries) if queries else 0.0
        return {'valid_receipts':len(valid),'total_receipts':len(receipts),'unique_query_ratio':round(ratio,3),'reproducible':len(valid)==len(receipts) and len(receipts)>0}

    def score_provenance_gate(self, dimension_scores:Dict[str,float], score_provenance:Dict[str,List[str]]|None) -> Dict[str,Any]:
        provenance=score_provenance or {}
        provided=[d for d in KILL_DIMENSIONS if d in dimension_scores]
        ungrounded=[d for d in provided if not provenance.get(d)]
        ratio=(len(provided)-len(ungrounded))/len(provided) if provided else 1.0
        return {'provided':len(provided),'ungrounded':ungrounded,'grounded_ratio':round(ratio,3),'pass':not ungrounded}

    def freshness_gate(self, evidence:List[Evidence], current_required_types:set[str]|None=None) -> Dict[str,Any]:
        required=current_required_types or {'official_product','regulator','standard','official_registry'}
        stale=[e.evidence_id for e in evidence if e.source_type in required and e.freshness!='CURRENT']
        return {'pass':not stale,'stale_material':stale}

    def evidence_dependency_graph(self, evidence:List[Evidence]) -> Dict[str,Any]:
        groups={}
        for e in evidence:
            groups.setdefault(e.independence_group,[]).append(e.evidence_id)
        return {'groups':groups,'independent_groups':len(groups),'largest_group':max((len(v) for v in groups.values()),default=0)}

    def decision_confidence(self, existence:Dict[str,Any], provenance_gate:Dict[str,Any], contradictions:int=0, freshness_ok:bool=True, reference_confidence:str='NONE') -> Dict[str,Any]:
        score=0
        score += 30 if existence.get('search_coverage',{}).get('complete') else 0
        health=existence.get('health',{})
        score += 25 if health.get('coverage')=='HIGH' else 15 if health.get('coverage')=='MEDIUM' else 5 if health.get('coverage')=='LOW' else 0
        score += 20 if provenance_gate.get('pass') else int(20*provenance_gate.get('grounded_ratio',0))
        score += 10 if freshness_ok else 0
        score += 10 if contradictions==0 else 0
        score += {'HIGH':5,'MEDIUM':3,'LOW':1,'NONE':0}.get(reference_confidence,0)
        band='HIGH' if score>=80 else 'MEDIUM' if score>=55 else 'LOW'
        return {'score':score,'band':band}

    def error_cost_gate(self, proposed_verdict:str, confidence_band:str, false_kill_cost:float, false_survival_cost:float) -> Dict[str,Any]:
        fk=max(0,float(false_kill_cost)); fs=max(0,float(false_survival_cost))
        if str(proposed_verdict).startswith('KILLED') and fk>2*max(fs,1e-9) and confidence_band!='HIGH':
            return {'final':'HOLD_ASYMMETRIC_ERROR_COST','reason':'FALSE_KILL_COST_HIGH_REQUIRES_HIGH_CONFIDENCE'}
        return {'final':proposed_verdict,'reason':'NO_OVERRIDE'}

    def degraded_mode(self, web_available:bool, patent_sources_available:bool, task_requires_existence:bool=True)->Dict[str,Any]:
        if task_requires_existence and (not web_available or not patent_sources_available):
            return {'mode':'DEGRADED','existence_verdict_allowed':False,'required':'HOLD_EXISTENCE_SEARCH_INCOMPLETE'}
        return {'mode':'NORMAL','existence_verdict_allowed':True}

    def assumption_ledger(self, assumptions: List[Dict[str,Any]]) -> Dict[str,Any]:
        rows=[]; fatal_open=[]
        for a in assumptions:
            status=a.get('status','UNKNOWN')
            criticality=a.get('criticality','MATERIAL')
            row={'assumption':a.get('assumption',''), 'status':status, 'criticality':criticality,
                 'evidence':a.get('evidence',[]), 'disproof_test':a.get('disproof_test')}
            rows.append(row)
            if criticality=='FATAL' and status not in ('SUPPORTED','PROVEN'):
                fatal_open.append(row['assumption'])
        return {'rows':rows,'fatal_open':fatal_open,'fatal_open_count':len(fatal_open)}

    def readiness_assessment(self, component_trls: Dict[str,int], advancement_difficulty:Dict[str,str]|None=None) -> Dict[str,Any]:
        if not component_trls:
            return {'system_trl':None,'weakest':[],'advancement_difficulty':advancement_difficulty or {},'status':'UNKNOWN'}
        vals={k:max(1,min(9,int(v))) for k,v in component_trls.items()}
        system=min(vals.values())
        weakest=[k for k,v in vals.items() if v==system]
        return {'system_trl':system,'components':vals,'weakest':weakest,
                'advancement_difficulty':advancement_difficulty or {},
                'status':'EARLY' if system<=3 else 'PROTOTYPE' if system<=6 else 'OPERATIONAL_MATURITY'}

    def reference_class(self, comparables: List[Dict[str,Any]]) -> Dict[str,Any]:
        if not comparables:
            return {'n':0,'confidence':'NONE','success_rate':None,'median_cost_ratio':None,'median_schedule_ratio':None}
        successes=[1 if c.get('success') else 0 for c in comparables if 'success' in c]
        costs=[float(c['cost_ratio']) for c in comparables if c.get('cost_ratio') is not None]
        sched=[float(c['schedule_ratio']) for c in comparables if c.get('schedule_ratio') is not None]
        n=len(comparables)
        return {'n':n,
                'confidence':'HIGH' if n>=20 else 'MEDIUM' if n>=8 else 'LOW',
                'success_rate':round(sum(successes)/len(successes),3) if successes else None,
                'median_cost_ratio':round(statistics.median(costs),3) if costs else None,
                'median_schedule_ratio':round(statistics.median(sched),3) if sched else None}

    def failure_tree(self, failure_modes: List[Dict[str,Any]]) -> Dict[str,Any]:
        paths=[]
        for f in failure_modes:
            sev=max(1,min(5,int(f.get('severity',3))))
            lik=max(1,min(5,int(f.get('likelihood',3))))
            det=max(1,min(5,int(f.get('detectability',3))))
            criticality=sev*lik
            priority=criticality*det
            paths.append({'mode':f.get('mode','UNKNOWN'),'cause':f.get('cause'),'effect':f.get('effect'),
                          'severity':sev,'likelihood':lik,'detectability':det,
                          'criticality':criticality,'test_priority':priority,
                          'single_point':bool(f.get('single_point',False))})
        paths.sort(key=lambda x:(x['single_point'],x['test_priority']),reverse=True)
        return {'paths':paths,'single_points':[p['mode'] for p in paths if p['single_point']],
                'top':paths[:5]}

    def cheapest_disproof(self, tests: List[Dict[str,Any]]) -> Dict[str,Any]:
        ranked=[]
        for t in tests:
            cost=max(0.01,float(t.get('cost',1)))
            time=max(0.01,float(t.get('time',1)))
            kill_power=max(0.0,min(1.0,float(t.get('kill_power',0.5))))
            independence=max(0.1,min(1.0,float(t.get('independence',0.5))))
            score=(kill_power*independence)/(math.sqrt(cost*time))
            ranked.append({**t,'disproof_efficiency':round(score,6)})
        ranked.sort(key=lambda x:x['disproof_efficiency'],reverse=True)
        return {'ranked':ranked,'first':ranked[0] if ranked else None}

    def market_evidence_level(self, signals: List[Dict[str,Any]]) -> Dict[str,Any]:
        # Decision-aid evidence ladder; not a universal scientific scale.
        levels={'OPINION':0,'STATED_INTEREST':1,'BEHAVIOR_SIGNAL':2,'COMMITMENT':3,'MONEY':4,'REPEAT_PAID_USE':5}
        best=0; best_type='NONE'
        for s in signals:
            typ=s.get('type','OPINION')
            lvl=levels.get(typ,0)
            if lvl>best: best=lvl; best_type=typ
        return {'level':best,'best_signal':best_type,'signals':len(signals),
                'status':'STRONG' if best>=4 else 'MEDIUM' if best>=2 else 'WEAK'}

    def economics_stress(self, scenarios: List[Dict[str,Any]]) -> Dict[str,Any]:
        out=[]
        for s in scenarios:
            revenue=float(s.get('revenue',0)); variable=float(s.get('variable_cost',0)); fixed=float(s.get('fixed_cost',0)); cac=float(s.get('cac',0))
            margin=revenue-variable-fixed-cac
            out.append({'name':s.get('name','scenario'),'net_contribution':round(margin,2),'survives':margin>0})
        return {'scenarios':out,'all_survive':bool(out) and all(x['survives'] for x in out),
                'worst':min(out,key=lambda x:x['net_contribution']) if out else None}

    def copycat_risk(self, commodity_fraction:float, proprietary_data:float, switching_cost:float, network_effect:float, regulatory_barrier:float, distribution_advantage:float) -> Dict[str,Any]:
        c=max(0,min(1,commodity_fraction)); defenses=[proprietary_data,switching_cost,network_effect,regulatory_barrier,distribution_advantage]
        defense=sum(max(0,min(1,float(x))) for x in defenses)/len(defenses)
        risk=max(0,min(1,0.65*c+0.35*(1-defense)))
        return {'risk':round(risk,3),'band':'EXTREME' if risk>=.8 else 'HIGH' if risk>=.6 else 'MEDIUM' if risk>=.35 else 'LOW'}

    def platform_absorption_risk(self, feature_adjacency:float, incumbent_reach:float, integration_advantage:float, monetization_conflict:float=0.0) -> Dict[str,Any]:
        vals=[max(0,min(1,float(x))) for x in [feature_adjacency,incumbent_reach,integration_advantage]]
        conflict=max(0,min(1,float(monetization_conflict)))
        risk=max(0,min(1,(sum(vals)/3)*(1-0.35*conflict)))
        return {'risk':round(risk,3),'band':'HIGH' if risk>=.65 else 'MEDIUM' if risk>=.35 else 'LOW'}

    def dependency_fragility(self, dependencies: List[Dict[str,Any]]) -> Dict[str,Any]:
        rows=[]
        for d in dependencies:
            concentration=max(0,min(1,float(d.get('concentration',0.5))))
            replaceability=max(0,min(1,float(d.get('replaceability',0.5))))
            control=max(0,min(1,float(d.get('control',0.5))))
            risk=0.5*concentration+0.3*(1-replaceability)+0.2*(1-control)
            rows.append({'dependency':d.get('name','UNKNOWN'),'risk':round(risk,3),'single_point':risk>=0.75})
        return {'rows':rows,'single_points':[r['dependency'] for r in rows if r['single_point']],
                'max_risk':max((r['risk'] for r in rows),default=0.0)}

    def timing_fit(self, technology_trl:int|None, market_readiness:float, infrastructure_readiness:float) -> Dict[str,Any]:
        if technology_trl is None: return {'status':'UNKNOWN','gap':None}
        tech=max(1,min(9,int(technology_trl)))/9
        market=max(0,min(1,float(market_readiness))); infra=max(0,min(1,float(infrastructure_readiness)))
        env=(market+infra)/2
        gap=round(tech-env,3)
        if tech<.45 and env>.7: status='TECH_TOO_EARLY'
        elif tech>.75 and env<.4: status='MARKET_TOO_EARLY'
        elif abs(gap)<=.25: status='ROUGHLY_ALIGNED'
        else: status='MISMATCH'
        return {'status':status,'gap':gap,'technology':round(tech,3),'environment':round(env,3)}

    def kill_score(self, dimension_scores: Dict[str,float], fatal_assumptions:int=0, single_point_failures:int=0) -> Dict[str,Any]:
        unknown=[d for d in KILL_DIMENSIONS if d not in dimension_scores]
        vals=[max(0.0,min(100.0,float(dimension_scores[d]))) for d in KILL_DIMENSIONS if d in dimension_scores]
        if not vals:
            return {'risk_score':None,'unknown_dimensions':unknown,'verdict':'UNKNOWN'}
        base=sum(vals)/len(vals)
        penalty=min(20, fatal_assumptions*10 + single_point_failures*5)
        risk=round(min(100,base+penalty),2)
        if fatal_assumptions>0:
            verdict='KILLED_FATAL_ASSUMPTION'
        elif unknown and len(unknown)>6:
            verdict='UNKNOWN_TOO_MANY_GAPS'
        elif risk>=82:
            verdict='KILLED'
        elif risk>=66:
            verdict='CRITICAL_REPAIR_REQUIRED'
        elif risk>=46:
            verdict='SURVIVES_WITH_MAJOR_RISK'
        else:
            verdict='SURVIVES_KILL_TEST'
        return {'risk_score':risk,'unknown_dimensions':unknown,'verdict':verdict,'penalty':penalty}

    def false_kill_defense(self, kill_result: Dict[str,Any], counterevidence_strength: float, unresolved_contradictions: int=0, independent_counter_sources:int=0) -> Dict[str,Any]:
        kv=kill_result.get('verdict')
        if not str(kv).startswith('KILLED'):
            return {'final':kv,'false_kill_review':'NOT_REQUIRED'}
        if unresolved_contradictions>0:
            return {'final':'HOLD_CONTRADICTIONS','false_kill_review':'BLOCK_KILL'}
        if counterevidence_strength>=0.70 and independent_counter_sources>=2:
            return {'final':'KILL_OVERTURNED_RETEST','false_kill_review':'COUNTEREVIDENCE_STRONG_INDEPENDENT'}
        if counterevidence_strength>=0.85 and independent_counter_sources<2:
            return {'final':'HOLD_COUNTEREVIDENCE_NOT_INDEPENDENT','false_kill_review':'SOURCE_DIVERSITY_REQUIRED'}
        return {'final':'KILLED_CONFIRMED','false_kill_review':'KILL_SURVIVED_APPEAL'}

    def saturation(self, rounds: List[Dict[str,Any]]) -> Dict[str,Any]:
        if len(rounds)<2:
            return {'saturated':False,'reason':'NEED_TWO_ROUNDS'}
        a,b=rounds[-2],rounds[-1]
        no_material=(a.get('new_material_findings',1)==0 and b.get('new_material_findings',1)==0)
        clean=(b.get('critical_contradictions',1)==0 and b.get('unknown_critical',1)==0 and b.get('freshness_ok',False))
        coverage_ok=bool(b.get('scope_complete',False))
        return {'saturated':bool(no_material and clean and coverage_ok),
                'reason':'TWO_CLEAN_ROUNDS_SCOPE_COMPLETE' if no_material and clean and coverage_ok else 'CONTINUE'}

    def staged_decision(self, final_verdict:str, cheapest_test:Dict[str,Any]|None, irreversible_cost:float=0.0) -> Dict[str,Any]:
        if final_verdict.startswith('KILLED'): return {'decision':'STOP_OR_REFRAME','spend':'MINIMUM'}
        if final_verdict.startswith('HOLD') or final_verdict in ('UNKNOWN_TOO_MANY_GAPS','CRITICAL_REPAIR_REQUIRED'):
            return {'decision':'RUN_CHEAPEST_DISPROOF','test':cheapest_test,'spend':'STAGED'}
        if final_verdict.startswith('SURVIVES'):
            return {'decision':'ADVANCE_ONE_EVIDENCE_GATE','test':cheapest_test,'spend':'STAGED','irreversible_cost':irreversible_cost}
        if 'RETEST' in final_verdict: return {'decision':'REPAIR_AND_RETEST','spend':'MINIMUM'}
        return {'decision':'REVIEW','spend':'MINIMUM'}

    def verdict(self, idea:Dict[str,Any], evidence:List[Evidence], searched_layers:List[str], dimension_scores:Dict[str,float],
                counterevidence_strength:float=0.0, unresolved_contradictions:int=0, independent_counter_sources:int=0,
                material_delta_score:float=0.0, material_delta_independent_evidence:int=0, assumptions:List[Dict[str,Any]]|None=None,
                failure_modes:List[Dict[str,Any]]|None=None, disproof_tests:List[Dict[str,Any]]|None=None,
                score_provenance:Dict[str,List[str]]|None=None, strict_score_provenance:bool=True,
                reference_confidence:str='NONE', false_kill_cost:float=1.0, false_survival_cost:float=1.0,
                search_receipts:List[Dict[str,Any]]|None=None, require_execution_receipts:bool=False) -> Dict[str,Any]:
        fp=self.fingerprint(idea)
        assumption_state=self.assumption_ledger(assumptions or [])
        ft=self.failure_tree(failure_modes or [])
        exists=self.existence_classification(evidence,searched_layers,material_delta_score,material_delta_independent_evidence)
        prov=self.score_provenance_gate(dimension_scores,score_provenance)
        fresh=self.freshness_gate(evidence)
        exec_gate=self.search_execution_gate(search_receipts or []) if require_execution_receipts else {'pass':True,'missing_layers':[],'failed_layers':[]}
        kill=self.kill_score(dimension_scores,assumption_state['fatal_open_count'],len(ft['single_points']))
        appeal=self.false_kill_defense(kill,counterevidence_strength,unresolved_contradictions,independent_counter_sources)
        final=appeal['final']
        # Fail-closed truth precedence: incomplete/stale/unverified evidence outranks destructive verdicts.
        if require_execution_receipts and not exec_gate['pass']:
            final='HOLD_SEARCH_NOT_EXECUTED'
        elif exists['status']=='UNKNOWN_INSUFFICIENT_SEARCH':
            final='HOLD_EXISTENCE_SEARCH_INCOMPLETE'
        elif not fresh['pass']:
            final='HOLD_STALE_MATERIAL_EVIDENCE'
        elif exists['status']=='EXISTS_CLOSE_DELTA_UNVERIFIED':
            final='HOLD_MATERIAL_DELTA_UNVERIFIED'
        elif strict_score_provenance and not prov['pass'] and exists['status']!='EXISTS_CLOSE_OR_SAME':
            final='HOLD_UNGROUNDED_SCORES'
        elif exists['status']=='EXISTS_CLOSE_OR_SAME' and material_delta_score<0.65 and final not in ('HOLD_CONTRADICTIONS','KILL_OVERTURNED_RETEST','HOLD_COUNTEREVIDENCE_NOT_INDEPENDENT'):
            final='KILLED_EXISTS_CLOSE_OR_SAME_WITHOUT_MATERIAL_DELTA'
        elif assumption_state['fatal_open_count'] and not final.startswith('HOLD'):
            final='KILLED_FATAL_ASSUMPTION'
        confidence=self.decision_confidence(exists,prov,unresolved_contradictions,fresh['pass'],reference_confidence)
        err=self.error_cost_gate(final,confidence['band'],false_kill_cost,false_survival_cost)
        final=err['final']
        cheapest=self.cheapest_disproof(disproof_tests or []).get('first')
        staged=self.staged_decision(final,cheapest,float(idea.get('irreversible_cost',0) or 0))
        return {
            'idea':fp,
            'existence':exists,
            'assumptions':assumption_state,
            'failure_tree':ft,
            'kill':kill,
            'score_provenance':prov,
            'freshness_gate':fresh,
            'search_execution_gate':exec_gate,
            'decision_confidence':confidence,
            'error_cost_gate':err,
            'false_kill_defense':appeal,
            'final_verdict':final,
            'novelty_claim_allowed':False,
            'staged_decision':staged,
            'required_next_action': self.next_action(final)
        }

    @staticmethod
    def next_action(v:str)->str:
        if v.startswith('KILLED'): return 'ARCHIVE_OR_REFRAME'
        if v.startswith('HOLD'): return 'RESEARCH_OR_TEST_MORE'
        if 'RETEST' in v: return 'REPAIR_AND_RETEST'
        if v.startswith('SURVIVES'): return 'ADVANCE_ONE_EVIDENCE_GATE'
        if v=='CRITICAL_REPAIR_REQUIRED': return 'RUN_CHEAPEST_DISPROOF'
        return 'REVIEW'

    @staticmethod
    def canonical_hash(obj:Any)->str:
        return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
