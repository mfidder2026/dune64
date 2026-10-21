; Hoofdstuk 1 - Aankomst (DESIGN.md §3.1)
; Startmenu, intro, Fort Varo, de eerste Tiende, en de engine-nodes (Tiende, overval, game over).
; Tekst: '|' = nieuwe regel, '||' = nieuwe pagina, {var} = getal, {loc} = huidige locatie.
; Tweetalig: SAY "nl" "en", OPT "nl" "en" doel, TEXT "nl" met eronder EN "en".

:intro
  SCENE ruimte
  SAY "ASHKARA - DE AMBERWOESTIJN" "ASHKARA - THE AMBER DESERT"
  MENU
    OPT "Nieuw spel" "New game"                    proloog
    OPT "Spel laden" "Load game"                   @LADEN
  END

:proloog
  SAY "ASHKARA, JAAR 812" "ASHKARA, YEAR 812"
  TEXT "De Hoge Raad stuurt Ilan Varo als landvoogd naar de amberwoestijn. Wie het amber beheerst, beheerst de sprongroutes van de Ring van Werelden."
    EN "The High Council sends Ilan Varo to the amber desert as its new governor. Whoever controls the amber controls the jump routes of the Ring of Worlds."
  TEXT "Onder het zand gloeit het amberiet. Boven het zand wacht het Mijnconsortium van gouverneur Kasimir Vorr."
    EN "Beneath the sand the amberite glows. Above the sand waits the Mining Consortium of Kasimir Vorr."
  JUMP raadzaal

; ---------------------------------------------------------------- raadzaal
:raadzaal
  SCENE raadzaal
  CHAR doran
  IF NOT doran_ontmoet
    SAY "DORAN KEYL"
    TEXT "Welkom op Fort Varo, heer. Het fort is van ons. Maar met veertig wachters houden we de Citadel van het Consortium niet lang op afstand."
      EN "Welcome to Fort Varo, sir. The fort is ours. But with forty guards we cannot keep the Consortium's Citadel at bay for long."
    SET doran_ontmoet
  END
  SAY "FORT VARO - RAADZAAL" "FORT VARO - COUNCIL HALL"
  MENU
    OPT "Praat met Doran" "Talk to Doran"          doran_praat
    OPT "Naar het balkon" "To the balcony"         balkon
    OPT "Communicatiekamer" "Comms room"           comms
    OPT "Hangar" "Hangar"                          hangar       IF vorr_eis
    OPT "Rust een dag" "Rest for a day"            @RUST        IF glider
    OPT "Opslaan / laden" "Save / load"            @OPSLAAN
  END

:doran_praat
  SAY "DORAN KEYL"
  MENU
    OPT "Over het Consortium" "About the Consortium" doran_consortium
    OPT "Over de Kethari" "About the Kethari"      doran_kethari
    OPT "Terug" "Back"                             raadzaal
  END

:doran_consortium
  SAY "DORAN KEYL"
  TEXT "Vorr noemt zich adviseur. Zijn huurlingen bewaken elke mijn tussen hier en de Citadel. Wij hebben muren, hij heeft schepen."
    EN "Vorr calls himself an adviser. His mercenaries guard every mine between here and the Citadel. We have walls, he has ships."
  JUMP doran_praat

:doran_kethari
  SAY "DORAN KEYL"
  TEXT "Het zandvolk leeft in de grotten van het zuiden. Ze vechten als de storm zelf. Geef ze een reden, heer, en ze vechten voor ons."
    EN "The sand people live in the caves of the south. They fight like the storm itself. Give them a reason, sir, and they will fight for us."
  JUMP doran_praat

; ---------------------------------------------------------------- balkon
:balkon
  IF h1_klaar AND NOT verklikker
    JUMP vesna_verklikker
  END
  SCENE balkon
  CHAR vesna
  IF NOT vesna_ontmoet
    SAY "VESNA ADAIR"
    TEXT "Vorr glimlacht te veel. Mijn mensen zien zijn schepen 's nachts landen bij de oude mijnen. Hij wacht op een fout van ons."
      EN "Vorr smiles too much. My people see his ships land at the old mines by night. He is waiting for us to make a mistake."
    SET vesna_ontmoet
  END
  SAY "FORT VARO - BALKON" "FORT VARO - BALCONY"
  MENU
    OPT "Praat met Vesna" "Talk to Vesna"          vesna_praat
    OPT "Terug naar de raadzaal" "Back to the hall" raadzaal
  END

:vesna_praat
  SAY "VESNA ADAIR"
  IF tiende_open
    TEXT "De Tiende is een strop: {tiende_eis} amber, uiterlijk dag {tiende_dag}. Haal je hem niet, dan krijgt Vorr het fort."
      EN "The Tithe is a noose: {tiende_eis} amber, by day {tiende_dag} at the latest. Miss it, and Vorr gets the fort."
  ELSE
    IF h1_klaar
      TEXT "Vorr laat zijn huurlingen los op de kampen die voor ons oogsten. Laat een kamp in de buurt strijd oefenen: dat houdt ze op afstand."
        EN "Vorr is sending his mercenaries after the camps that harvest for us. Have a nearby camp train for battle: that keeps them away."
    ELSE
      TEXT "Ga naar de communicatiekamer. Vorr wil je spreken, en hij wacht niet graag."
        EN "Go to the comms room. Vorr wants to speak with you, and he does not like to wait."
    END
  END
  JUMP balkon

; ---------------------------------------------------------------- comms
:comms
  SCENE comms
  CHAR vorr
  IF NOT vorr_eis
    SAY "GOUVERNEUR VORR" "GOVERNOR VORR"
    TEXT "De Raad verwacht de eerste Tiende, landvoogd: 500 amber binnen 15 dagen. Ik zou het jammer vinden als u zou falen."
      EN "The Council expects the first Tithe, governor: 500 amber within 15 days. It would be a pity if you were to fail."
    SET vorr_eis
    TIENDE 500 15
  END
  SAY "COMMUNICATIEKAMER" "COMMS ROOM"
  MENU
    OPT "Tiende verschepen" "Ship the Tithe"       tiende       IF tiende_open AND amber >= tiende_eis
    OPT "Vraag naar de Tiende" "Ask about the Tithe" tiende_info IF tiende_open
    OPT "Terug naar de raadzaal" "Back to the hall" raadzaal
  END

:tiende_info
  SAY "GOUVERNEUR VORR" "GOVERNOR VORR"
  TEXT "{tiende_eis} amber, landvoogd, uiterlijk op dag {tiende_dag}. U heeft er nu {amber}. Vandaag is het dag {day}."
    EN "{tiende_eis} amber, governor, by day {tiende_dag} at the latest. You have {amber} now. Today is day {day}."
  JUMP comms

:tiende
  CALL @TIENDE
  SAY "GOUVERNEUR VORR" "GOVERNOR VORR"
  IF h1_klaar
    TEXT "Ontvangen. U leert snel, landvoogd."
      EN "Received. You learn quickly, governor."
    JUMP comms
  END
  TEXT "Op tijd, landvoogd. De Raad is tevreden. Voorlopig. De volgende Tiende is groter: 900 amber, binnen 15 dagen."
    EN "On time, governor. The Council is satisfied. For now. The next Tithe is larger: 900 amber, within 15 days."
  SET h1_klaar
  SET f_overvallen
  TIENDE 900 15
  CHAR none
  SAY "HOOFDSTUK 1 VOLTOOID" "CHAPTER 1 COMPLETE"
  TEXT "Ilan Varo heeft de eerste Tiende betaald. Maar in de woestijn roert zich iets: het Consortium begint de kampen te overvallen.||Wordt vervolgd in hoofdstuk 2: Het Zandvolk."
    EN "Ilan Varo has paid the first Tithe. But something stirs in the desert: the Consortium has begun to raid the camps.||To be continued in chapter 2: The Sand People."
  JUMP comms

:tiende_waarschuwing
  SCENE comms
  CHAR vorr
  SAY "GOUVERNEUR VORR" "GOVERNOR VORR"
  TEXT "U bent te laat met de Tiende, landvoogd. De Raad geeft u drie dagen uitstel. Tot dag {tiende_dag}. Niet langer."
    EN "Your Tithe is late, governor. The Council grants you three more days. Until day {tiende_dag}. No longer."
  RETURN

:overval
  SCENE oogst
  CHAR none
  SAY "OVERVAL!" "RAID!"
  TEXT "Huurlingen van het Consortium hebben {plaats_overval_loc} overvallen. De oogstmachine brandt, de Kethari zijn gevlucht of gevangen.||Een kamp dat strijd oefent, beschermt de kampen binnen zes dagmarsen."
    EN "Consortium mercenaries have raided {plaats_overval_loc}. The harvester burns, the Kethari have fled or been taken.||A camp that trains for battle protects the camps within six marches."
  RETURN

:gameover_bezet
  SCENE storm
  CHAR none
  SAY "HET ZAND ZWIJGT" "THE SAND FALLS SILENT"
  TEXT "Geen enkel kamp volgt je nog. Zonder de Kethari is Ashkara verloren."
    EN "Not a single camp follows you any more. Without the Kethari, Ashkara is lost."
  CALL @GAMEOVER

:gameover_tiende
  SCENE comms
  CHAR vorr
  SAY "GOUVERNEUR VORR" "GOVERNOR VORR"
  TEXT "Geen Tiende. De Raad trekt uw aanstelling in, landvoogd. Fort Varo valt toe aan het Consortium. Ik zal het goed beheren."
    EN "No Tithe. The Council revokes your appointment, governor. Fort Varo passes to the Consortium. I shall manage it well."
  CALL @GAMEOVER

; ---------------------------------------------------------------- hangar
:hangar
  IF KAMP fort = BEZET
    JUMP fort_bezet
  END
  IF h1_klaar AND NOT mardo_water
    JUMP mardo_water_h2
  END
  SCENE hangar
  CHAR mardo
  IF NOT mardo_ontmoet
    SAY "DR. ILSE MARDO"
    TEXT "Uw glider staat klaar. Ik meet al jaren de diepe waterlagen. Ze zakken sneller dan het Consortium toegeeft."
      EN "Your glider is ready. I have been measuring the deep water layers for years. They are sinking faster than the Consortium admits."
    TEXT "Zoek de Kethari in de Rode Kloof, ten zuidoosten van het fort. Zonder hen haalt u nooit genoeg amber boven. Neem deze oogstmachine mee: geef hem aan een kamp dat voor u oogst."
      EN "Find the Kethari in the Red Gorge, southeast of the fort. Without them you will never bring up enough amber. Take this harvester: give it to a camp that harvests for you."
    SET mardo_ontmoet
    SET glider
    SET oogstmachine
  END
  SAY "FORT VARO - HANGAR"
  MENU
    OPT "Opstijgen (kaart)" "Take off (map)"       @KAART
    OPT "Praat met Mardo" "Talk to Mardo"          mardo_praat
    OPT "Naar de raadzaal" "To the council hall"   raadzaal
  END

:mardo_praat
  SAY "DR. ILSE MARDO"
  TEXT "Amber vindt u het makkelijkst bij de lichtende velden: 's nachts gloeit het zand daar oranje. Een kamp dat oogst put de bodem langzaam uit."
    EN "Amber is easiest to find at the glowing fields: at night the sand there glows orange. A camp that harvests slowly drains the ground."
  JUMP hangar
