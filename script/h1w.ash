; Hoofdstuk 1 - Aankomst, deel 2: de woestijn (DESIGN.md §3.1)
; De Rode Kloof (Saira, Tarik) en de generieke locaties (kampen, voorposten, Citadel, Mer).
; Deze nodes zijn aankomst-nodes uit data/locations.json; de engine laadt dit blok bij aankomst.

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
    MENU
      OPT "Ik breng water mee."    saira_water
      OPT "Ik heb krijgers nodig." saira_krijgers
      OPT "Omdat ik het beveel."   saira_bevel
    END
  END
  SAY "DE RODE KLOOF"
  MENU
    OPT "Ga de grot binnen"      grot
    OPT "Praat met Saira"        saira_praat
    OPT "Kaart"                  @KAART
  END

:saira_water
  TRUST 10
  SET saira_ontmoet
  SET saira_mee
  SAY "SAIRA"
  TEXT "Water. Dat hebben de stedelingen ons nooit gebracht. Kom binnen. En als je wilt vliegen: ik ken de kampen beter dan je kaart."
  JUMP kloof

:saira_krijgers
  TRUST 5
  SET saira_ontmoet
  SAY "SAIRA"
  TEXT "Eerlijk, tenminste. Tarik zal willen weten wat wij ervoor terugkrijgen."
  JUMP kloof

:saira_bevel
  TRUST -10
  SET saira_ontmoet
  SAY "SAIRA"
  TEXT "Bevelen. Het Consortium beveelt ook. Ga maar naar binnen, dan hoor je wat Tarik daarvan vindt."
  JUMP kloof

:saira_praat
  SAY "SAIRA"
  IF saira_mee
    TEXT "Vlieg laag over de duinen, dan zie ik de rook van de kampen. Samen vinden we ze sneller."
  ELSE
    TEXT "Laat eerst zien dat je te vertrouwen bent. Dan vlieg ik misschien met je mee."
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
    SET tarik_ontmoet
  END
  SAY "TARIK UR-KESH"
  MENU
    OPT "Vraag om krijgers"      tarik_krijgers  IF NOT KAMP HIER = BONDGENOOT
    OPT "Geef een taak"          @TAAK           IF KAMP HIER = BONDGENOOT
    OPT "Vraag naar het water"   tarik_water
    OPT "Bied een geschenk aan"  @GESCHENK
    OPT "Vraag naar andere kampen" tarik_kampen
    OPT "Status van het kamp"    @STATUS
    OPT "Rust een dag"           @RUST
    OPT "Vertrek"                kloof
  END

:tarik_krijgers
  SAY "TARIK UR-KESH"
  IF NOT f_tarik_zegen
    IF VERTROUWEN >= 50
      TEXT "Je brengt water en je luistert. Goed. Je hebt mijn zegen, landvoogd. De andere kampen zullen het horen."
      SET f_tarik_zegen
    ELSE
      TEXT "Woorden zijn zand, landvoogd. Laat zien wat je voor ons doet."
      JUMP grot
    END
  END
  CALL @WERVEN
  JUMP grot

:tarik_water
  TRUST 5
  SAY "TARIK UR-KESH"
  TEXT "Onder het zand stroomde ooit water. De mijnen van het Consortium drinken het op. Zonder water geen groen, zonder groen geen toekomst."
  JUMP grot

:tarik_kampen
  SAY "TARIK UR-KESH"
  IF f_tarik_zegen
    TEXT "Er zijn twaalf kampen tussen de Citadel en de zoutvlakte. Vlieg laag. Wie mijn zegen draagt, wordt gehoord."
  ELSE
    TEXT "Andere kampen? Die praten pas met je als ik het goed vind."
  END
  JUMP grot

; ---------------------------------------------------------------- generieke locaties
:kamp
  IF KAMP HIER = BEZET
    JUMP kamp_bezet
  END
  SCENE grot
  CHAR none
  SAY "KAMP {loc}"
  MENU
    OPT "Praat met de oudste"    @PRAAT
    OPT "Bied water aan"         @GESCHENK    IF NOT KAMP HIER = BONDGENOOT
    OPT "Vraag om krijgers"      @WERVEN      IF NOT KAMP HIER = BONDGENOOT
    OPT "Geef een taak"          @TAAK        IF KAMP HIER = BONDGENOOT
    OPT "Status van het kamp"    @STATUS
    OPT "Rust een dag"           @RUST
    OPT "Kaart"                  @KAART
  END

:kamp_bezet
  SCENE grot
  CHAR none
  SAY "{loc} - BEZET"
  TEXT "Soldaten van het Consortium bewaken de ingang. De Kethari van {loc} zijn gevangen of gevlucht. Alleen met krijgers krijg je dit kamp terug."
  MENU
    OPT "Bevrijden"              @GEVECHT
    OPT "Kaart"                  @KAART
  END

:voorpost
  SCENE vesting
  CHAR none
  SAY "{loc}"
  TEXT "Een voorpost van het Consortium. Geschut op de muren, patrouilles in het zand. Met wachters alleen kom je hier niet binnen."
  MENU
    OPT "Aanvallen"              @GEVECHT
    OPT "Kaart"                  @KAART
  END

:citadel
  SCENE vesting
  CHAR none
  SAY "DE CITADEL"
  TEXT "De Citadel van Kasimir Vorr. Hoge muren, zwaar geschut. Nog lang niet."
  MENU
    OPT "Kaart"                  @KAART
  END

:mer
  SCENE woestijn
  CHAR none
  SAY "ZOUTVLAKTE MER"
  TEXT "Lege kramen in het zout. De handelaars van Mer komen pas als er iets te verdienen valt."
  MENU
    OPT "Kaart"                  @KAART
  END
