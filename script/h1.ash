; Hoofdstuk 1 - Aankomst (DESIGN.md §3.1)
; Intro, Fort Varo, de Rode Kloof (Saira, Tarik), generieke kampen en de eerste Tiende.
; Tekst: '|' = nieuwe regel, '||' = nieuwe pagina, {var} = getal, {loc} = huidige locatie.

:intro
  SCENE ruimte
  SAY "ASHKARA, JAAR 812"
  TEXT "De Hoge Raad stuurt Ilan Varo als landvoogd naar de amberwoestijn. Wie het amber beheerst, beheerst de sprongroutes van de Ring van Werelden."
  TEXT "Onder het zand gloeit het amberiet. Boven het zand wacht het Mijnconsortium van gouverneur Kasimir Vorr."
  JUMP raadzaal

; ---------------------------------------------------------------- raadzaal
:raadzaal
  SCENE raadzaal
  CHAR doran
  IF NOT doran_ontmoet
    SAY "DORAN KEYL"
    TEXT "Welkom op Fort Varo, heer. Het fort is van ons. Maar met veertig wachters houden we de Citadel van het Consortium niet lang op afstand."
    SET doran_ontmoet
  END
  SAY "FORT VARO - RAADZAAL"
  MENU
    OPT "Praat met Doran"        doran_praat
    OPT "Naar het balkon"        balkon
    OPT "Communicatiekamer"      comms
    OPT "Hangar"                 hangar       IF vorr_eis
    OPT "Rust een dag"           @RUST        IF glider
  END

:doran_praat
  SAY "DORAN KEYL"
  MENU
    OPT "Over het Consortium"    doran_consortium
    OPT "Over de Kethari"        doran_kethari
    OPT "Terug"                  raadzaal
  END

:doran_consortium
  SAY "DORAN KEYL"
  TEXT "Vorr noemt zich adviseur. Zijn huurlingen bewaken elke mijn tussen hier en de Citadel. Wij hebben muren, hij heeft schepen."
  JUMP doran_praat

:doran_kethari
  SAY "DORAN KEYL"
  TEXT "Het zandvolk leeft in de grotten van het zuiden. Ze vechten als de storm zelf. Geef ze een reden, heer, en ze vechten voor ons."
  JUMP doran_praat

; ---------------------------------------------------------------- balkon
:balkon
  SCENE balkon
  CHAR vesna
  IF NOT vesna_ontmoet
    SAY "VESNA ADAIR"
    TEXT "Vorr glimlacht te veel. Mijn mensen zien zijn schepen 's nachts landen bij de oude mijnen. Hij wacht op een fout van ons."
    SET vesna_ontmoet
  END
  SAY "FORT VARO - BALKON"
  MENU
    OPT "Praat met Vesna"        vesna_praat
    OPT "Terug naar de raadzaal" raadzaal
  END

:vesna_praat
  SAY "VESNA ADAIR"
  IF tiende_open
    TEXT "De Tiende is een strop: {tiende_eis} amber, uiterlijk dag {tiende_dag}. Haal je hem niet, dan krijgt Vorr het fort."
  ELSE
    IF h1_klaar
      TEXT "De Raad is tevreden, voor nu. Vorr niet. Hij laat zijn schepen vaker vliegen."
    ELSE
      TEXT "Ga naar de communicatiekamer. Vorr wil je spreken, en hij wacht niet graag."
    END
  END
  JUMP balkon

; ---------------------------------------------------------------- comms
:comms
  SCENE comms
  CHAR vorr
  IF NOT vorr_eis
    SAY "GOUVERNEUR VORR"
    TEXT "De Raad verwacht de eerste Tiende, landvoogd: 500 amber binnen 15 dagen. Ik zou het jammer vinden als u zou falen."
    SET vorr_eis
    TIENDE 500 15
  END
  SAY "COMMUNICATIEKAMER"
  MENU
    OPT "Tiende verschepen"      tiende       IF tiende_open AND amber >= tiende_eis
    OPT "Vraag naar de Tiende"   tiende_info  IF tiende_open
    OPT "Terug naar de raadzaal" raadzaal
  END

:tiende_info
  SAY "GOUVERNEUR VORR"
  TEXT "{tiende_eis} amber, landvoogd, uiterlijk op dag {tiende_dag}. U heeft er nu {amber}. Vandaag is het dag {day}."
  JUMP comms

:tiende
  CALL @TIENDE
  SAY "GOUVERNEUR VORR"
  IF h1_klaar
    TEXT "Ontvangen. U leert snel, landvoogd."
    JUMP comms
  END
  TEXT "Op tijd, landvoogd. De Raad is tevreden. Voorlopig. De volgende Tiende is groter: 900 amber, binnen 15 dagen."
  SET h1_klaar
  TIENDE 900 15
  CHAR none
  SAY "HOOFDSTUK 1 VOLTOOID"
  TEXT "Ilan Varo heeft de eerste Tiende betaald. Maar in de woestijn roert zich iets.||Wordt vervolgd in hoofdstuk 2: Het Zandvolk."
  JUMP comms

:tiende_waarschuwing
  SCENE comms
  CHAR vorr
  SAY "GOUVERNEUR VORR"
  TEXT "U bent te laat met de Tiende, landvoogd. De Raad geeft u drie dagen uitstel. Tot dag {tiende_dag}. Niet langer."
  RETURN

:gameover_tiende
  SCENE comms
  CHAR vorr
  SAY "GOUVERNEUR VORR"
  TEXT "Geen Tiende. De Raad trekt uw aanstelling in, landvoogd. Fort Varo valt toe aan het Consortium. Ik zal het goed beheren."
  CALL @GAMEOVER

; ---------------------------------------------------------------- hangar
:hangar
  SCENE hangar
  CHAR mardo
  IF NOT mardo_ontmoet
    SAY "DR. ILSE MARDO"
    TEXT "Uw glider staat klaar. Ik meet al jaren de diepe waterlagen. Ze zakken sneller dan het Consortium toegeeft."
    TEXT "Zoek de Kethari in de Rode Kloof, ten zuidoosten van het fort. Zonder hen haalt u nooit genoeg amber boven. Neem deze oogstmachine mee: geef hem aan een kamp dat voor u oogst."
    SET mardo_ontmoet
    SET glider
    SET oogstmachine
  END
  SAY "FORT VARO - HANGAR"
  MENU
    OPT "Opstijgen (kaart)"      @KAART
    OPT "Praat met Mardo"        mardo_praat
    OPT "Naar de raadzaal"       raadzaal
  END

:mardo_praat
  SAY "DR. ILSE MARDO"
  TEXT "Amber vindt u het makkelijkst bij de lichtende velden: 's nachts gloeit het zand daar oranje. Een kamp dat oogst put de bodem langzaam uit."
  JUMP hangar
