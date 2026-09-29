# NexStudio V1 presenter presets. Source this file, then call female_look / male_look.
PV1="$(cd "$(dirname "${BASH_SOURCE[0]}")/scripts" && pwd)"; export PV1
export MH_ROOT=${MH_ROOT:-/home/ubuntu/mh_assets}
source "$PV1/env.sh"; source "$PV1/styles.sh"

# female_look HAIRSTYLE HAIRCOL SKIN LIP NECK DRESS DRESSCOL
#   HAIRSTYLE: long bob bangs bun braid       (each carries its own earring)
#   HAIRCOL:   "" (auburn) 1C1714 3B2418 D8B77A B9B8B5 or any hex
#   SKIN:      F7E1D3 (fair) "" (light) E0B48F (medium) C99A6E (tan) 9E6B4A (brown) 6A4431 (deep) or any hex
#   LIP:       "" (soft rose) B3202A 8A2A4E E0664F B8826F or any hex
#   NECK:      none fine pendant pearls choker scarf
#   DRESS:     mindfront_f_dress_11 mindfront_f_dress_09 mindfront_f_dress_07 punkduck_black_cocktail_dress punkduck_middle_length_qipao
female_look(){ style "$1"; export HCOL=$2 STONE=$3 LIPC=$4 NECK=${5/none/} DRESS=$6 DCOL=$7 MODF=female.py
  case $6 in punkduck_middle_length_qipao) export DMINISL=200;; *) export DMINISL=0;; esac; }

# male_look O1..O5 [WATCH]   WATCH: analog digital smart chrono dress
male_look(){ export DBTN=0 EST=none TUCK=0 SIDES=1 HDYE= MODF=modM.py
  case $1 in
   O1) export HAIR=afro01 HCOL=1C1714 STONE=5C3A28 LIPC=5A3328 WATCH=analog MG="namuhekam_male_polo_shirt=2E3A55,mindfront_male_trousers_1=3A3A40,mindfront_shoes_oxford_male=3A2A20";;
   O2) export HAIR=short01 HCOL=C9A366 STONE=E3B994 LIPC=A87868 WATCH=digital MG="toigo_basic_tucked_t-shirt=EDEBE6,elvs_jeans_straight_leg=2E3A55,punkduck_comfortable_sneakers=ECEAE4";;
   O3) export HAIR=elvs_maxwell_hair HCOL=5A3A24 STONE=C99A6E LIPC=9A6656 WATCH=dress MG="elvs_male_shirt_untucked_bd1=A9C4DE,mindfront_male_trousers_2=B59A6E,mindfront_shoes_monk_strap_male=4A2E1E";;
   O4) export HAIR=elvs_braided_rows HCOL=141212 HDYE=8A1F3C STONE=8D5A3F LIPC=6E4436 WATCH=smart MG="mindfront_knitted_sweater_01=6B2E2E,punkduck_male_classic_jeans=3A4660,culturalibre_sneakers=E8E6E0";;
   O5) export HAIR=elvs_grump_hair HCOL=8F9096 STONE=B07F57 LIPC=8A5A48 WATCH=chrono MG="toigo_fisherman_sweater=D8CFBE,toigo_wool_pants=3A3A40,mindfront_shoes_oxford_male=3A2A20";;
  esac
  [ -n "$2" ] && export WATCH=$2
  export MH_COMMUNITY_ASSETS=$(ls -d "$MH_ROOT"/*/hair/$HAIR | head -1 | sed 's#/hair/.*##'); }
