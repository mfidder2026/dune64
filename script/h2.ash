; Hoofdstuk 2 - Het Zandvolk, en hoofdstuk 3 - Verraad (DESIGN.md §3.1)
; H2 begint na de eerste Tiende: Vesna's verklikker, Mardo over het water, Saira's nachtscène.
; H3 is een tijd-event op dag 34: aanval op Fort Varo, vlucht door de storm naar de Rode Kloof.
; Tweetalig: SAY "nl" "en", OPT "nl" "en" doel, TEXT "nl" met eronder EN "en".

ON_DAY 34 verraad

; ---------------------------------------------------------------- H2: Vesna en de verklikker
:vesna_verklikker
  SCENE balkon
  CHAR vesna
  SAY "VESNA ADAIR"
  TEXT "Ik heb hem. Een klerk uit de communicatiekamer stuurt Vorr elke nacht onze vluchtplannen. Daarom weten zijn huurlingen precies waar onze kampen oogsten. Wat doen we met hem?"
    EN "I have him. A clerk in the comms room sends Vorr our flight plans every night. That is how his mercenaries know exactly where our camps harvest. What do we do with him?"
  MENU
    OPT "Laat hem arresteren" "Have him arrested"          verklikker_arrest
    OPT "Voer hem valse berichten" "Feed him false reports" verklikker_vals
  END

:verklikker_arrest
  SET verklikker
  SAY "VESNA ADAIR"
  TEXT "Hij zit vast. Vorr zal snel merken dat zijn oog dicht is. Wees voorzichtig: een blinde wolf bijt eerder."
    EN "He is locked up. Vorr will soon notice that his eye is shut. Be careful: a blind wolf bites sooner."
  JUMP balkon

:verklikker_vals
  SET verklikker
  SET verklikker_vals
  SAY "VESNA ADAIR"
  TEXT "Slim. Hij vertelt Vorr voortaan wat wij willen. Als het ooit misgaat, geeft dat ons een voorsprong."
    EN "Clever. From now on he tells Vorr what we want him to. If things ever go wrong, that gives us a head start."
  JUMP balkon

; ---------------------------------------------------------------- H2: Mardo en het water
:mardo_water_h2
  SCENE hangar
  CHAR mardo
  SAY "DR. ILSE MARDO"
  TEXT "Mijn metingen kloppen niet met de cijfers van het Consortium. Hun mijnen pompen het grondwater weg. Over tien jaar is er niets meer over."
    EN "My measurements do not match the Consortium's figures. Their mines are pumping the groundwater away. In ten years there will be nothing left."
  TEXT "Maar er is hoop. Een windvanger haalt vocht uit de nachtlucht. Met genoeg windvangers wordt de woestijn weer groen. Ik werk aan een ontwerp."
    EN "But there is hope. A windcatcher draws moisture from the night air. With enough windcatchers the desert turns green again. I am working on a design."
  SET mardo_water
  JUMP hangar

; ---------------------------------------------------------------- H2: Saira en de lichtende velden
:saira_nacht
  SCENE nacht
  CHAR none
  SAY "SAIRA"
  TEXT "Kijk. Daar, waar het zand oranje gloeit: de lichtende velden. Daar ligt het amber vlak onder de oppervlakte."
    EN "Look. There, where the sand glows orange: the glowing fields. That is where the amber lies just beneath the surface."
  TEXT "Mijn grootmoeder zei dat het zand ooit groen was, en dat het amber de tranen van de planeet zijn. Twee kampen wonen bij de velden: Oud-Khesset en Daresh."
    EN "My grandmother said the sand was green once, and that the amber is the planet's tears. Two camps live by the fields: Oud-Khesset and Daresh."
  SET saira_nacht
  IF KAMP khesset = ONBEKEND
    LOCSTATUS khesset BEKEND
  END
  IF KAMP daresh = ONBEKEND
    LOCSTATUS daresh BEKEND
  END
  JUMP kloof

; ---------------------------------------------------------------- H3: Verraad
:verraad
  SCENE nacht
  CHAR none
  SAY "VERRAAD!" "BETRAYAL!"
  TEXT "Midden in de nacht: explosies bij de poort. Schepen van het Consortium landen op de binnenplaats van Fort Varo. Vorr heeft zijn masker laten vallen."
    EN "In the middle of the night: explosions at the gate. Consortium ships land in the courtyard of Fort Varo. Vorr has dropped his mask."
  IF verklikker_vals
    TEXT "Dankzij de valse berichten van Vesna's verklikker kwam de aanval een uur later dan Vorr wilde. Iedereen haalt de hangar."
      EN "Thanks to the false reports of Vesna's informant, the attack came an hour later than Vorr intended. Everyone makes it to the hangar."
  ELSE
    TEXT "Doran houdt de trap vast terwijl jij naar de hangar rent. Een schot raakt hem in de schouder; je sleept hem mee de glider in."
      EN "Doran holds the stairs while you run for the hangar. A shot hits him in the shoulder; you drag him into the glider."
  END
  SCENE storm
  SAY "DE STORM" "THE STORM"
  TEXT "Met Doran, Vesna en Mardo aan boord vlucht je de zandstorm in. De glider schudt en kraakt. Alleen de Kethari kunnen je nu nog opvangen."
    EN "With Doran, Vesna and Mardo aboard you flee into the sandstorm. The glider shakes and groans. Only the Kethari can take you in now."
  SET f_verraad
  SET f_overvallen
  CLR tiende_open
  LOCSTATUS fort BEZET
  LOCSTATUS urkesh BONDGENOOT
  LET loc urkesh
  SAY "HOOFDSTUK 3: VERRAAD" "CHAPTER 3: BETRAYAL"
  TEXT "Fort Varo is gevallen. Er is geen Tiende meer: de Raad heeft je opgegeven. Vanaf nu is de Rode Kloof je basis.||Bevrijd Ashkara: verover de voorposten met de Kethari, of breng het water terug. De handelaars van Mer verkopen nu wapens."
    EN "Fort Varo has fallen. There is no more Tithe: the Council has given up on you. From now on the Red Gorge is your base.||Free Ashkara: take the outposts with the Kethari, or bring back the water. The traders of Mer now sell weapons."
  JUMP grot

:fort_bezet
  SCENE vesting
  CHAR none
  SAY "FORT VARO - BEZET" "FORT VARO - OCCUPIED"
  TEXT "Op de muren van Fort Varo wappert de vlag van het Consortium. Een kleine wacht houdt het fort. Met krijgers kun je het terugnemen."
    EN "The Consortium's flag flies on the walls of Fort Varo. A small guard holds the fort. With warriors you can take it back."
  MENU
    OPT "Bevrijden" "Liberate"                      @GEVECHT
    OPT "Kaart" "Map"                               @KAART
  END
