# Music Industry Skills

아티스트, 앨범, 캠페인, 차트, 소셜 반응과 음악 시장을 조사하기 위한
Codex 스킬 모음입니다.

질문마다 필요한 API와 웹 소스를 조합하고, 서로 다른 집계 기준의 숫자를
무리하게 합치지 않으며, 중요한 주장에는 확인 가능한 출처를 남기는 것을
목표로 합니다.

## 가장 쉬운 설치 방법

Codex에서 새 작업을 열고 아래 문장을 그대로 보내세요.

```text
https://github.com/mintplo/music-industry-skills/tree/main/skills/music/research-music 에서 research-music 스킬을 설치해줘.
```

설치가 끝나면 **다음 메시지부터** `$research-music`을 붙여 사용할 수 있습니다.

```text
$research-music 코르티스 새 앨범의 콘셉트와 초기 반응을 조사해줘.
```

## 이런 질문에 사용할 수 있습니다

```text
$research-music 이 아티스트의 전체 앨범과 발매 시기를 정리해줘.

$research-music 이번 컴백의 티저와 프로모션 전략을 시간순으로 분석해줘.

$research-music 두 아티스트의 최근 앨범 성과를 같은 기준으로 비교해줘.

$research-music 최근 일본 시장에서 성장 중인 K-pop 아티스트와 근거를 찾아줘.
```

질문의 범위에 맞춰 필요한 조사 경로만 선택하므로, 매번 정해진 형식의 긴
리포트를 만들지는 않습니다.

## 현재 제공하는 스킬

### `research-music`

음악 산업 전반을 조사하는 범용 리서치 스킬입니다.

- 아티스트·앨범·곡·트랙리스트·디스코그래피 조사
- 컴백 롤아웃·티저·뮤직비디오·프로모션 캠페인 분석
- 판매량·차트·스트리밍·영상·공개 소셜 신호 확인
- 아티스트 또는 발매작 비교
- 국가·장르·플랫폼·시장 동향 조사
- 공식 자료, 음악 API, 웹 검색과 허용된 크롤링 결과의 교차 확인

[스킬 설명 보기](./skills/music/research-music/SKILL.md) ·
[지원 소스 보기](./skills/music/research-music/providers/CATALOG.md)

## 데이터와 API에 관하여

웹 검색과 공개 데이터만으로도 바로 시작할 수 있습니다. 질문에 따라
MusicBrainz, Apple Music, Wikidata, YouTube, Spotify, Circle Chart, Oricon,
공식 아티스트 페이지와 보도자료 등을 선택적으로 조합합니다.

다만 모든 데이터를 무료로 얻을 수 있는 것은 아닙니다.

- Spotify의 일부 데이터는 개발자 앱과 인증 정보가 필요할 수 있습니다.
- 판매량·차트의 상세 데이터는 국가, 기간, 상품 또는 유료 계약에 따라
  접근 범위가 달라집니다.
- 현재 조회한 SNS 수치는 과거 특정 시점의 수치로 간주하지 않습니다.
- 사이트 정책이나 이용 약관이 허용하지 않는 우회 수집을 전제로 하지 않습니다.

스킬은 값을 추측해 채우는 대신, 확인된 정보와 접근할 수 없는 정보를 구분해
답하도록 설계되어 있습니다.

## 저장소를 직접 설치하는 방법

터미널과 Git에 익숙하다면 저장소를 복제한 뒤 활성 스킬을 Codex에 연결할 수
있습니다.

```bash
git clone https://github.com/mintplo/music-industry-skills.git
cd music-industry-skills
./scripts/link-skills.sh
```

이 방식은 `~/.codex/skills/research-music`에 저장소를 가리키는 링크를 만듭니다.
이후 저장소에서 `git pull`을 실행하면 스킬도 함께 업데이트됩니다. 이미 같은
이름의 다른 스킬이 설치되어 있으면 안전을 위해 덮어쓰지 않습니다.

## 저장소 구조

```text
skills/
  music/
    research-music/     # 현재 사용 가능한 범용 음악 리서치 스킬
  in-progress/          # 아직 배포하지 않는 실험적 스킬
  deprecated/           # 이전 버전 보관
scripts/
  list-skills.sh        # 배포 대상 스킬 확인
  link-skills.sh        # 로컬 Codex에 활성 스킬 연결
tests/                  # 스킬 계약과 보조 수집기의 테스트
```

새로운 데이터 제공자나 조사 유형은 `research-music` 안의 provider 문서와 recipe를
추가하는 방식으로 확장합니다. 별도의 좁은 스킬은 사용 흐름이 실제로 분리될 때만
추가할 계획입니다.

## 유의 사항

이 저장소는 리서치를 돕는 도구이며, 각 데이터 제공자의 라이선스나 이용 약관을
대체하지 않습니다. 중요한 의사결정에는 답변에 연결된 원문과 데이터의 시장,
집계 기간, 측정 기준을 함께 확인하세요.
