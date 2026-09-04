// F1: categoriesマスタの初期投入（詳細設計仕様書 4-3の14分野）。
// `npx prisma db seed` から実行される。

import { prisma } from "../lib/prisma";

const CATEGORY_NAMES = [
  "行政・公的機関",
  "金融・投資",
  "政治・地域自治",
  "商業・小売・飲食",
  "建設・インフラ・交通",
  "農林水産",
  "観光・宿泊",
  "メディア・クリエイティブ",
  "IT・テクノロジー",
  "スポーツ",
  "福祉・医療・介護",
  "教育",
  "コンサルティング・中間支援",
  "ライフスタイル・専門職",
];

async function main() {
  for (const [index, name] of CATEGORY_NAMES.entries()) {
    await prisma.category.upsert({
      where: { name },
      update: { sortOrder: index },
      create: { name, sortOrder: index },
    });
  }
  console.log(`Seeded ${CATEGORY_NAMES.length} categories.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
