; Hoofdstuk 1 - Aankomst, deel 2: de woestijn (DESIGN.md §3.1)
; De Rode Kloof (Saira, Tarik) en de generieke locaties (kampen, voorposten, Citadel, Mer).
; Deze nodes zijn aankomst-nodes uit data/locations.json; de engine laadt dit blok bij aankomst.
; Tweetalig: SAY "nl" "en", OPT "nl" "en" doel, TEXT "nl" met eronder EN "en".

; ---------------------------------------------------------------- de Rode Kloof (kamp Ur-Kesh)
:kloof
  IF KAMP HIER = BEZET
    JUMP kamp_bezet
  END
  SCENE kloof
  CHAR saira
  IF NOT saira_ontmoet
    SAY "SAIRA"
    TEXT "Je draagt laarzen van de stad en ruikt naar olie. Waarom zou Tarik met een landvoogd praten?"
      EN "You wear city boots and smell of oil. Why would Tarik talk to a governor?"
    MENU
      OPT "Ik breng water mee." "I bring water."     saira_water
      OPT "Ik heb krijgers nodig." "I need warriors." saira_krijgers
      OPT "Omdat ik het beveel." "Because I say so." saira_bevel
    END
  END
  SAY "DE RODE KLOOF" "THE RED GORGE"
  MENU
    OPT "Ga de grot binnen" "Enter the cave"       grot
    OPT "Praat met Saira" "Talk to Saira"          saira_praat
    OPT "Kaart" "Map"                              @KAART
  END

:saira_water
  TRUST 10
  SET saira_ontmoet
  SET saira_mee
  SAY "SAIRA"
  TEXT "Water. Dat hebben de stedelingen ons nooit gebracht. Kom binnen. En als je wilt vliegen: ik ken de kampen beter dan je kaart."
    EN "Water. The city people never brought us that. Come in. And if you want to fly: I know the camps better than your map does."
  JUMP kloof

:saira_krijgers
  TRUST 5
  SET saira_ontmoet
  SAY "SAIRA"
  TEXT "Eerlijk, tenminste. Tarik zal willen weten wat wij ervoor terugkrijgen."
    EN "Honest, at least. Tarik will want to know what we get in return."
  JUMP kloof

:saira_bevel
  TRUST -10
  SET saira_ontmoet
  SAY "SAIRA"
  TEXT "Bevelen. Het Consortium beveelt ook. Ga maar naar binnen, dan hoor je wat Tarik daarvan vindt."
    EN "Orders. The Consortium gives orders too. Go inside, then, and hear what Tarik thinks of that."
  JUMP kloof

:saira_praat
  SAY "SAIRA"
  IF saira_mee
    TEXT "Vlieg laag over de duinen, dan zie ik de rook van de kampen. Samen vinden we ze sneller."
      EN "Fly low over the dunes and I will spot the smoke of the camps. Together we will find them faster."
  ELSE
    TEXT "Laat eerst zien dat je te vertrouwen bent. Dan vlieg ik misschien met je mee."
      EN "First show me you can be trusted. Then maybe I will fly with you."
  END
  JUMP kloof

:grot
  IF KAMP HIER = BEZET
    JUMP kamp_bezet
  END
  SCENE grot
  CHAR tarik
  IF NOT tarik_ontmoet
    SAY "TARIK UR-KESH"
    TEXT "Een landvoogd in mijn grot. Het Consortium nam ons water en onze velden. Wat kom jij nemen?"
      EN "A governor in my cave. The Consortium took our water and our fields. What have you come to take?"
    SET tarik_ontmoet
  END
  SAY "TARIK UR-KESH"
  MENU
    OPT "Vraag om krijgers" "Ask for warriors"     tarik_krijgers  IF NOT KAMP HIER = BONDGENOOT
    OPT "Geef een taak" "Give a task"              @TAAK           IF KAMP HIER = BONDGENOOT
    OPT "Vraag naar het water" "Ask about water"   tarik_water
    OPT "Bied een geschenk aan" "Offer a gift"     @GESCHENK
    OPT "Vraag naar andere kampen" "Ask about other camps" tarik_kampen
    OPT "Status van het kamp" "Camp status"        @STATUS
    OPT "Rust een dag" "Rest for a day"            @RUST
    OPT "Vertrek" "Leave"                          kloof
  END

:tarik_krijgers
  SAY "TARIK UR-KESH"
  IF NOT f_tarik_zegen
    IF VERTROUWEN >= 50
      TEXT "Je brengt water en je luistert. Goed. Je hebt mijn zegen, landvoogd. De andere kampen zullen het horen."
        EN "You bring water and you listen. Good. You have my blessing, governor. The other camps will hear of it."
      SET f_tarik_zegen
    ELSE
      TEXT "Woorden zijn zand, landvoogd. Laat zien wat je voor ons doet."
        EN "Words are sand, governor. Show us what you will do for us."
      JUMP grot
    END
  END
  CALL @WERVEN
  JUMP grot

:tarik_water
  TRUST 5
  SAY "TARIK UR-KESH"
  TEXT "Onder het zand stroomde ooit water. De mijnen van het Consortium drinken het op. Zonder water geen groen, zonder groen geen toekomst."
    EN "Water once flowed beneath the sand. The Consortium's mines drink it dry. No water, no green; no green, no future."
  JUMP grot

:tarik_kampen
  SAY "TARIK UR-KESH"
  IF f_tarik_zegen
    TEXT "Er zijn twaalf kampen tussen de Citadel en de zoutvlakte. Vlieg laag. Wie mijn zegen draagt, wordt gehoord."
      EN "There are twelve camps between the Citadel and the salt flat. Fly low. Whoever bears my blessing will be heard."
  ELSE
    TEXT "Andere kampen? Die praten pas met je als ik het goed vind."
      EN "Other camps? They will only talk to you once I approve."
  END
  JUMP grot

; ---------------------------------------------------------------- generieke locaties
:kamp
  IF KAMP HIER = BEZET
    JUMP kamp_bezet
  END
  SCENE grot
  CHAR none
  SAY "KAMP {loc}" "CAMP {loc}"
  MENU
    OPT "Praat met de oudste" "Talk to the elder"  @PRAAT
    OPT "Bied water aan" "Offer water"             @GESCHENK    IF NOT KAMP HIER = BONDGENOOT
    OPT "Vraag om krijgers" "Ask for warriors"     @WERVEN      IF NOT KAMP HIER = BONDGENOOT
    OPT "Geef een taak" "Give a task"              @TAAK        IF KAMP HIER = BONDGENOOT
    OPT "Status van het kamp" "Camp status"        @STATUS
    OPT "Rust een dag" "Rest for a day"            @RUST
    OPT "Kaart" "Map"                              @KAART
  END

:kamp_bezet
  SCENE grot
  CHAR none
  SAY "{loc} - BEZET" "{loc} - OCCUPIED"
  TEXT "Soldaten van het Consortium bewaken de ingang. De Kethari van {loc} zijn gevangen of gevlucht. Alleen met krijgers krijg je dit kamp terug."
    EN "Consortium soldiers guard the entrance. The Kethari of {loc} have been taken or have fled. Only warriors can win this camp back."
  MENU
    OPT "Bevrijden" "Liberate"                     @GEVECHT
    OPT "Kaart" "Map"                              @KAART
  END

:voorpost
  SCENE vesting
  CHAR none
  SAY "{loc}"
  TEXT "Een voorpost van het Consortium. Geschut op de muren, patrouilles in het zand. Met wachters alleen kom je hier niet binnen."
    EN "A Consortium outpost. Guns on the walls, patrols in the sand. With guards alone you will never get in."
  MENU
    OPT "Aanvallen" "Attack"                       @GEVECHT
    OPT "Kaart" "Map"                              @KAART
  END

:citadel
  SCENE vesting
  CHAR none
  SAY "DE CITADEL" "THE CITADEL"
  TEXT "De Citadel van Kasimir Vorr. Hoge muren, zwaar geschut. Nog lang niet."
    EN "The Citadel of Kasimir Vorr. High walls, heavy guns. Not for a long time yet."
  MENU
    OPT "Kaart" "Map"                              @KAART
  END

:mer
  SCENE woestijn
  CHAR none
  SAY "ZOUTVLAKTE MER" "MER SALT FLAT"
  TEXT "Lege kramen in het zout. De handelaars van Mer komen pas als er iets te verdienen valt."
    EN "Empty stalls in the salt. The traders of Mer only come when there is profit to be made."
  MENU
    OPT "Kaart" "Map"                              @KAART
  END
