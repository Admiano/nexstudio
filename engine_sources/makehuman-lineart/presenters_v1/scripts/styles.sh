style(){ unset HAIR; export SIDES=1 TUCK=1 EST=hoop HR=0.011 SNX=24 SNZ=4
case $1 in
 long) ;;
 bob) export HAIR=toigo_blunt_bob EST=bar TZT=0.015 BARW=0.0021 SMIN=9 ;;
 bangs) export HAIR=toigo_blunt_bob_with_bangs EST=stud STR=0.0052 TZT=0.0 EY=0.0 ;;
 bun) export HAIR=rehmanpolanski_hair_bun_brown SIDES=1,-1 TUCK=0 EST=hoop HR=0.016 ;;
 braid) export HAIR=elvs_french_braid_variation EST=drop SNX=10 SNZ=3 SW=2.4 HLW=2.6 ;;
esac; }
