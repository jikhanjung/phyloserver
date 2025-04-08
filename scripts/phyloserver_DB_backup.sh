#!/bin/bash
ENV_FILE="$(dirname "$0")/../phyloserver/.env"
if [ -f "$ENV_FILE" ]; then
  #export $(grep -v '^#' "$ENV_FILE" | xargs)
  set -a
  source "$ENV_FILE"
  set +a  
else
  echo "❌ .env 파일이 존재하지 않습니다: $ENV_FILE"
  exit 1
fi
# 설정
DB_NAME="phyloserver"
#DB_USER="$DB_USER"
#DB_PASSWORD="$DB_PASSWORD"
BACKUP_DIR="/home/paleoadmin/db_backups"
DATE=$(date +"%Y-%m-%d_%H-%M")
FILENAME="${DB_NAME}_${DATE}.sql.gz"
DEST="${BACKUP_DIR}/${FILENAME}"

# 디렉토리 확인
mkdir -p "$BACKUP_DIR"

# 백업 수행
mysqldump -u "$DB_USER" -p"$DB_PASSWORD" --single-transaction --routines --triggers "$DB_NAME" | gzip > "$DEST"
if [ $? -eq 0 ]; then
  echo "✅ 백업 완료: $DEST"
else
  echo "❌ 백업 실패!"
  exit 1
fi

# 오래된 백업 정리
echo "🧹 오래된 백업 정리 중..."

cd "$BACKUP_DIR" || exit 1

# 날짜 파싱을 쉽게 하기 위해 파일 이름 리스트를 가져옴
for file in ${DB_NAME}_*.sql.gz; do
  # 날짜 추출 (예: 2024-04-08_03-00 → 2024 04 08)
  file_date_str=$(echo "$file" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
  file_date=$(date -d "$file_date_str" +%s)
  today=$(date +%s)
  age_days=$(( (today - file_date) / 86400 ))

  year=$(date -d "$file_date_str" +%Y)
  month=$(date -d "$file_date_str" +%m)
  day=$(date -d "$file_date_str" +%d)

  # 7일 이내는 무조건 보관
  if [ "$age_days" -le 7 ]; then
    continue
  fi

  # 1년 넘은 경우: 해당 연도 첫 백업만 보관
  if [ "$age_days" -gt 365 ]; then
    # 해당 연도 첫 백업인지 확인
    is_first_of_year=$(ls ${DB_NAME}_${year}-*.sql.gz | sort | head -n 1)
    if [ "$file" != "$is_first_of_year" ]; then
      echo "🗑️ 삭제 (1년 초과): $file"
      rm "$file"
    fi
    continue
  fi

  # 1개월 넘은 경우: 해당 월의 첫 백업만 보관
  if [ "$age_days" -gt 30 ]; then
    month_tag="${year}-${month}"
    is_first_of_month=$(ls ${DB_NAME}_${month_tag}-*.sql.gz | sort | head -n 1)
    if [ "$file" != "$is_first_of_month" ]; then
      echo "🗑️ 삭제 (1개월 초과): $file"
      rm "$file"
    fi
    continue
  fi

  # 나머지(1주 ~ 1달): 전부 삭제
  echo "🗑️ 삭제 (1주 초과): $file"
  rm "$file"
done
