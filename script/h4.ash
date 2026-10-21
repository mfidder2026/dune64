; Hoofdstuk 4 - Opstand, en hoofdstuk 5 - De Citadel (DESIGN.md §3.1)
; Doran terug (dag 40), windvangers van Mardo (dag 44), uitslagen van gevechten, vergroening en
; de twee eindes. De uitslagen zijn engine-nodes (battle.c, sim.c); {plaats_gevecht_loc} = de plek.
; Tweetalig: SAY "nl" "en", OPT "nl" "en" doel, TEXT "nl" met eronder EN "en".

ON_DAY 40 doran_terug
ON_DAY 44 mardo_windvanger

; ---------------------------------------------------------------- H4: tijd-events
:doran_terug
  SCENE grot
  CHAR none
  SAY "DORAN KEYL"
  TEXT "Mijn schouder houdt het weer, landvoogd. Laat mij je krijgers trainen: kampen die strijd oefenen, worden nu twee keer zo snel sterk."
    EN "My shoulder holds again, governor. Let me train your warriors: camps that train for battle now grow strong twice as fast."
  SET f_doran_terug
  RETURN

:mardo_windvanger
  SCENE oase
  CHAR none
  SAY "DR. ILSE MARDO"
  TEXT "Het ontwerp is klaar: een windvanger. De handelaars van Mer kunnen ze bouwen, voor 150 amber per stuk. Zet er een bij een kamp en geef het de taak Vergroenen."
    EN "The design is ready: a windcatcher. The traders of Mer can build them, for 150 amber each. Place one at a camp and give it the task Make it green."
  TEXT "Gebieden die groen worden, geeft het Consortium op: daar valt voor hen niets meer te halen. Is genoeg van Ashkara groen, dan heeft de Citadel geen reden meer om te blijven."
    EN "The Consortium abandons areas that turn green: there is nothing left for them to take. Once enough of Ashkara is green, the Citadel has no reason to stay."
  SET f_windvanger
  RETURN

; ---------------------------------------------------------------- H4: gesprekken in de grot
:doran_h4
  SCENE grot
  CHAR none
  SAY "DORAN KEYL"
  TEXT "Een voorpost valt niet met moed alleen. Kies je sterkste kampen, koop wapens in Mer en laat ze oefenen. En ga zelf alleen mee als het echt moet: sneuvel jij, dan is alles voorbij."
    EN "An outpost does not fall to courage alone. Choose your strongest camps, buy weapons at Mer and let them train. And only come along yourself if you must: if you fall, it is all over."
  JUMP grot

:mardo_h4
  SCENE grot
  CHAR none
  SAY "DR. ILSE MARDO"
  IF f_windvanger
    TEXT "Elke windvanger maakt zijn gebied elke dag iets groener. Rond groene kampen houdt het Consortium het niet vol. Groen %: {groen}."
      EN "Every windcatcher makes its area a little greener each day. Around green camps the Consortium cannot hold out. Green %: {groen}."
  ELSE
    TEXT "Ik werk nog aan het ontwerp van de windvanger. Geef me een paar dagen."
      EN "I am still working on the windcatcher design. Give me a few days."
  END
  JUMP grot

; ---------------------------------------------------------------- uitslagen
:gevecht_gewonnen
  SCENE vesting
  CHAR none
  SAY "OVERWINNING!" "VICTORY!"
  TEXT "{plaats_gevecht_loc} is gevallen. De gevangenen sluiten zich bij je aan; het is nu een kamp van de Kethari."
    EN "{plaats_gevecht_loc} has fallen. The prisoners join you; it is now a Kethari camp."
  IF f_citadel
    TEXT "Een ondervraagde officier praat: de Citadel heeft nog maar een generator voor haar schilden. Een aanval op de Citadel kan nu slagen."
      EN "An interrogated officer talks: the Citadel has only one generator left for its shields. An attack on the Citadel can succeed now."
  ELSE
    TEXT "De ondervraagde officier zwijgt nog over de Citadel. Misschien praat de volgende."
      EN "The interrogated officer still says nothing about the Citadel. Perhaps the next one will talk."
  END
  RETURN

:kamp_bevrijd
  SCENE grot
  CHAR none
  SAY "BEVRIJD!" "LIBERATED!"
  TEXT "De soldaten zijn verdreven. {plaats_gevecht_loc} is weer vrij, en de Kethari vergeten dat niet."
    EN "The soldiers have been driven out. {plaats_gevecht_loc} is free again, and the Kethari will not forget it."
  RETURN

:gevecht_verloren
  SCENE vesting
  CHAR none
  SAY "VERSLAGEN" "DEFEATED"
  TEXT "De aanval op {plaats_gevecht_loc} is mislukt. De helft van je krijgers is gevallen of gevangen. Train, bewapen, en probeer het opnieuw."
    EN "The attack on {plaats_gevecht_loc} has failed. Half of your warriors have fallen or been captured. Train, arm, and try again."
  RETURN

:gameover_gesneuveld
  SCENE storm
  CHAR none
  SAY "GESNEUVELD" "FALLEN"
  TEXT "Ilan Varo sneuvelde aan de voet van {plaats_gevecht_loc}. Zonder landvoogd valt de opstand uiteen."
    EN "Ilan Varo fell at the foot of {plaats_gevecht_loc}. Without its governor, the uprising falls apart."
  CALL @GAMEOVER

:voorpost_verlaten
  SCENE oase
  CHAR none
  SAY "HET GROEN WINT" "THE GREEN WINS"
  TEXT "Het Consortium heeft {plaats_gevecht_loc} verlaten. Waar gras groeit, valt geen amber te halen. De Kethari trekken erin."
    EN "The Consortium has abandoned {plaats_gevecht_loc}. Where grass grows, there is no amber to take. The Kethari move in."
  RETURN

; ---------------------------------------------------------------- H5: de eindes
:einde_groen
  SCENE oase
  CHAR none
  SAY "DE CITADEL GEEFT OP" "THE CITADEL SURRENDERS"
  TEXT "Overal tussen de duinen groeit gras. De mijnen staan stil, de schepen van het Consortium vertrekken een voor een. Kasimir Vorr vertrekt als laatste, zonder een woord."
    EN "Grass grows everywhere between the dunes. The mines stand still, and the Consortium's ships leave one by one. Kasimir Vorr is the last to go, without a word."
  TEXT "Op dag {day} valt de eerste regen in honderd jaar. Ashkara is vrij: niet door wapens, maar door water."
    EN "On day {day} the first rain in a hundred years falls. Ashkara is free: not by weapons, but by water."
  CALL @EINDE

:einde_militair
  SCENE vesting
  CHAR none
  SAY "DE CITADEL IS GEVALLEN" "THE CITADEL HAS FALLEN"
  TEXT "De schilden doven, de poorten breken. De Kethari stromen de Citadel binnen. Kasimir Vorr wordt in de boeien naar de Hoge Raad gestuurd."
    EN "The shields fade, the gates break. The Kethari pour into the Citadel. Kasimir Vorr is sent to the High Council in chains."
  TEXT "Op dag {day} hijsen de Kethari hun vlag op de Citadel. Ashkara is vrij. Nu begint het echte werk: het water terugbrengen."
    EN "On day {day} the Kethari raise their banner over the Citadel. Ashkara is free. Now the real work begins: bringing back the water."
  CALL @EINDE
