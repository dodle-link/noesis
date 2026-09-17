// ===== Shared header/footer injection (avoids duplicating markup across pages) =====
(function injectLayout() {
  const page = location.pathname.split("/").pop() || "index.html";
  const bookHref = page === "rooms.html" ? "#booking-marker" : "rooms.html";

  const navItems = [
    { href: "index.html", label: "Home" },
    { href: "rooms.html", label: "Rooms" },
    { href: "amenities.html", label: "Amenities" },
    { href: "faq.html", label: "FAQ" },
    { href: "contact.html", label: "Contact" },
  ];

  const navLinksHTML = navItems
    .map((item) => `<li><a href="${item.href}"${item.href === page ? ' class="active"' : ""}>${item.label}</a></li>`)
    .join("");

  const headerHTML = `
<header class="site-header">
  <nav class="nav">
    <a href="index.html" class="logo">HEIVA</a>
    <div class="nav-links-container">
      <ul class="nav-links">${navLinksHTML}</ul>
    </div>
    <div class="header-buttons">
      <button class="theme-toggle" type="button" aria-label="Switch to dark mode" aria-pressed="false">
        <span class="theme-toggle-icon" aria-hidden="true">&#9788;</span>
      </button>
      <label class="language-switcher">
        <span class="sr-only">Language</span>
        <select class="language-select" aria-label="Select language">
          <option value="en">English</option>
          <option value="ja">日本語</option>
          <option value="zh">中文</option>
          <option value="th">ไทย</option>
        </select>
      </label>
      <a href="${bookHref}" class="nav-book">Book Now</a>
    </div>
    <button class="nav-toggle" aria-label="Toggle navigation">
      <span></span><span></span><span></span>
    </button>
  </nav>
</header>`;

  const footerHTML = `
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <a href="index.html" class="footer-logo">Heiwa Hotel</a>
        <p>123 Shoreline Avenue, Coastal Bay, CA 90210</p>
        <div class="social-links">
          <a href="#" aria-label="Facebook">f</a>
          <a href="#" aria-label="Instagram">i</a>
          <a href="#" aria-label="Twitter">t</a>
        </div>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li>+1 (555) 012-3456</li>
          <li>stay@heiwahotel.com</li>
        </ul>
      </div>
      <div>
        <h4>Hours</h4>
        <ul>
          <li>Front Desk: 24/7</li>
          <li>Check-in: 3:00 PM</li>
          <li>Check-out: 11:00 AM</li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>&copy; 2026 Heiwa Hotel. All rights reserved.</span>
      <span>Privacy Policy · Terms of Service</span>
    </div>
  </div>
</footer>`;

  const headerMount = document.getElementById("site-header");
  const footerMount = document.getElementById("site-footer");
  if (headerMount) headerMount.outerHTML = headerHTML;
  if (footerMount) footerMount.outerHTML = footerHTML;
})();

// ===== Theme toggle =====
const themeToggle = document.querySelector(".theme-toggle");
const savedTheme = localStorage.getItem("heiwa-theme");

function setTheme(isDark) {
  document.body.classList.toggle("dark-mode", isDark);
  if (!themeToggle) return;
  themeToggle.setAttribute("aria-pressed", String(isDark));
  themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
  themeToggle.querySelector(".theme-toggle-icon").textContent = isDark ? "\u263E" : "\u2600";
}

setTheme(savedTheme === "dark");

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const isDark = !document.body.classList.contains("dark-mode");
    setTheme(isDark);
    localStorage.setItem("heiwa-theme", isDark ? "dark" : "light");
    translatePage(localStorage.getItem("heiwa-language") || "en");
  });
}

// ===== Custom select (progressive enhancement of native <select>) =====
const customSelectRefreshers = [];

// ===== Language selector =====
const languageSelects = document.querySelectorAll(".language-select");
const savedLanguage = localStorage.getItem("heiwa-language") || "en";
const translationRows = [
  ["Switch to dark mode", "ダークモードに切り替え", "切换到深色模式", "เปลี่ยนเป็นโหมดมืด"],
  ["Switch to light mode", "ライトモードに切り替え", "切换到浅色模式", "เปลี่ยนเป็นโหมดสว่าง"],
  ["Toggle navigation", "ナビゲーションを切り替え", "切换导航", "เปิด/ปิดเมนูนำทาง"],
  ["Facebook", "Facebook", "Facebook", "Facebook"],
  ["Instagram", "Instagram", "Instagram", "Instagram"],
  ["Twitter", "Twitter", "Twitter", "Twitter"],
  ["Heiwa Hotel — Minimal Comfort by the Sea", "Heiwaホテル — 海辺のミニマルな快適さ", "Heiwa酒店 — 海滨简约舒适", "โรงแรม Heiwa — ความสบายเรียบง่ายริมทะเล"],
  ["Rooms & Suites — Heiwa Hotel", "客室とスイート — Heiwaホテル", "客房与套房 — Heiwa酒店", "ห้องพักและห้องสวีท — โรงแรม Heiwa"],
  ["Amenities & Services — Heiwa Hotel", "設備とサービス — Heiwaホテル", "设施与服务 — Heiwa酒店", "สิ่งอำนวยความสะดวกและบริการ — โรงแรม Heiwa"],
  ["Contact & Booking — Heiwa Hotel", "お問い合わせと予約 — Heiwaホテル", "联系与预订 — Heiwa酒店", "ติดต่อและจองห้องพัก — โรงแรม Heiwa"],
  ["FAQ — Heiwa Hotel", "よくある質問 — Heiwaホテル", "常见问题 — Heiwa酒店", "คำถามที่พบบ่อย — โรงแรม Heiwa"],
  ["Heiwa Hotel offers minimal, peaceful stays with modern rooms, amenities, and easy online booking.", "Heiwaホテルは、モダンな客室と設備、簡単なオンライン予約で、静かでミニマルな滞在をご提供します。", "Heiwa酒店提供简约宁静的住宿、现代客房和设施，并支持便捷的在线预订。", "Heiwa Hotel ให้บริการเข้าพักอย่างสงบเรียบง่าย พร้อมห้องพักทันสมัย สิ่งอำนวยความสะดวก และการจองออนไลน์ที่ง่ายดาย"],
  ["Browse Heiwa Hotel's rooms and suites, check rates, and book your stay online.", "Heiwaホテルの客室とスイートをご覧いただき、料金を確認してオンラインでご予約ください。", "浏览Heiwa酒店的客房与套房，查看价格并在线预订。", "ดูห้องพักและห้องสวีทของ Heiwa Hotel ตรวจสอบราคา และจองออนไลน์"],
  ["Discover Heiwa Hotel's amenities including dining, spa, pool, gym, and guest services.", "ダイニング、スパ、プール、ジム、ゲストサービスなど、Heiwaホテルの施設をご紹介します。", "探索Heiwa酒店的餐饮、水疗、泳池、健身房和住客服务。", "ค้นพบสิ่งอำนวยความสะดวกของ Heiwa Hotel ทั้งร้านอาหาร สปา สระว่ายน้ำ ฟิตเนส และบริการผู้เข้าพัก"],
  ["Contact Heiwa Hotel for reservations, questions, or special requests. Find our address, phone, and location map.", "ご予約、ご質問、特別なご要望はHeiwaホテルまでお問い合わせください。住所、電話番号、地図もご確認いただけます。", "如需预订、咨询或特殊要求，请联系Heiwa酒店。查看我们的地址、电话和位置地图。", "ติดต่อ Heiwa Hotel สำหรับการจอง คำถาม หรือคำขอพิเศษ ดูที่อยู่ เบอร์โทรศัพท์ และแผนที่ได้ที่นี่"],
  ["Frequently asked questions about booking, rooms, amenities, and policies at Heiwa Hotel.", "Heiwaホテルの予約、客室、施設、ポリシーに関するよくある質問です。", "关于Heiwa酒店预订、客房、设施和政策的常见问题。", "คำถามที่พบบ่อยเกี่ยวกับการจอง ห้องพัก สิ่งอำนวยความสะดวก และนโยบายของ Heiwa Hotel"],
  ["Home", "ホーム", "首页", "หน้าหลัก"],
  ["Rooms", "客室", "客房", "ห้องพัก"],
  ["Amenities", "設備", "设施", "สิ่งอำนวยความสะดวก"],
  ["FAQ", "よくある質問", "常见问题", "คำถามที่พบบ่อย"],
  ["Contact", "お問い合わせ", "联系我们", "ติดต่อเรา"],
  ["Dark", "ダーク", "深色", "มืด"],
  ["Light", "ライト", "浅色", "สว่าง"],
  ["Language", "言語", "语言", "ภาษา"],
  ["Select language", "言語を選択", "选择语言", "เลือกภาษา"],
  ["Book Now", "今すぐ予約", "立即预订", "จองเลย"],
  ["Est. 1998 · Oceanfront Retreat", "1998年創業 · 海辺の隠れ家", "始于1998年 · 海滨度假胜地", "ก่อตั้งปี 1998 · ที่พักริมทะเล"],
  ["Quiet Rooms. Calm Mind. Heiwa Hotel.", "静かな客室。穏やかな心。平和ホテル。", "安静客房，平静心境。Heiwa酒店。", "ห้องพักเงียบสงบ ใจผ่อนคลาย โรงแรม Heiwa"],
  ["A minimal hotel designed around rest — clean rooms, honest service, and a view of the sea.", "休息を中心に考えたミニマルなホテル。清潔な客室、誠実なサービス、海の眺めをご提供します。", "以休息为核心设计的简约酒店，拥有整洁客房、真诚服务和海景。", "โรงแรมมินิมอลที่ออกแบบมาเพื่อการพักผ่อน ห้องพักสะอาด บริการจริงใจ และวิวทะเล"],
  ["View Rooms", "客室を見る", "查看客房", "ดูห้องพัก"],
  ["Check Availability", "空室を確認", "查询空房", "ตรวจสอบห้องว่าง"],
  ["Check-in", "チェックイン", "入住", "เช็กอิน"],
  ["Check-out", "チェックアウト", "退房", "เช็กเอาต์"],
  ["Guests", "宿泊人数", "客人数", "ผู้เข้าพัก"],
  ["1 Guest", "1名", "1位客人", "1 คน"],
  ["2 Guests", "2名", "2位客人", "2 คน"],
  ["3 Guests", "3名", "3位客人", "3 คน"],
  ["4+ Guests", "4名以上", "4位以上客人", "4 คนขึ้นไป"],
  ["Room Type", "客室タイプ", "房型", "ประเภทห้อง"],
  ["Standard Room", "スタンダードルーム", "标准客房", "ห้องสแตนดาร์ด"],
  ["Deluxe Room", "デラックスルーム", "豪华客房", "ห้องดีลักซ์"],
  ["Ocean Suite", "オーシャンスイート", "海景套房", "ห้องสวีทวิวทะเล"],
  ["About Heiwa", "Heiwaについて", "关于Heiwa", "เกี่ยวกับ Heiwa"],
  ["A hotel built around simplicity", "シンプルさを大切にしたホテル", "以简约为核心的酒店", "โรงแรมที่สร้างขึ้นเพื่อความเรียบง่าย"],
  ["Heiwa means peace — and that's the only agenda here. Twenty-eight rooms, a small restaurant, a quiet terrace, and staff who remember your name. No clutter, no noise, just a comfortable place to stay.", "Heiwaは平和を意味します。ここで大切なのはそれだけです。28室の客室、小さなレストラン、静かなテラス、そしてお名前を覚えているスタッフ。余計なものも騒音もない、心地よい滞在場所です。", "Heiwa意为和平，这里唯一的宗旨就是让您安心。28间客房、小餐厅、安静露台，以及记得您名字的员工。没有杂乱，没有喧嚣，只有舒适的住宿体验。", "Heiwa หมายถึงสันติภาพ และนั่นคือสิ่งเดียวที่เราใส่ใจ มีห้องพัก 28 ห้อง ร้านอาหารเล็ก ๆ ระเบียงเงียบสงบ และพนักงานที่จำชื่อคุณได้ ไม่มีความวุ่นวายหรือเสียงรบกวน มีเพียงการเข้าพักที่แสนสบาย"],
  ["Rooms & Suites", "客室とスイート", "客房与套房", "ห้องพักและห้องสวีท"],
  ["Rooms & Suites", "客室とスイート", "客房与套房", "ห้องพักและห้องสวีท"],
  ["Guest Rating", "ゲスト評価", "住客评分", "คะแนนผู้เข้าพัก"],
  ["Years Open", "営業年数", "开业年数", "ปีที่เปิดให้บริการ"],
  ["Stay With Us", "当ホテルでの滞在", "入住我们酒店", "พักกับเรา"],
  ["Featured Rooms", "おすすめの客室", "精选客房", "ห้องพักแนะนำ"],
  ["A small selection of our most-loved rooms and suites.", "人気の客室とスイートを厳選してご紹介します。", "精选我们最受欢迎的客房和套房。", "คัดสรรห้องพักและห้องสวีทที่ผู้เข้าพักชื่นชอบ"],
  ["City View", "シティビュー", "城市景观", "วิวเมือง"],
  ["Garden View", "ガーデンビュー", "花园景观", "วิวสวน"],
  ["Ocean View", "オーシャンビュー", "海景", "วิวทะเล"],
  ["A calm, well-lit room with everything you need and nothing you don't.", "必要なものをすべて備え、余計なものを省いた、明るく穏やかな客室です。", "宁静明亮的客房，配备您所需的一切，不多不少。", "ห้องพักสงบสว่าง พร้อมทุกสิ่งที่จำเป็นและไม่มีสิ่งเกินจำเป็น"],
  ["More space, a reading corner, and a deep soaking tub.", "ゆとりの空間、読書コーナー、深めのバスタブを備えています。", "更大的空间、阅读角和深泡浴缸。", "พื้นที่กว้างขึ้น มุมอ่านหนังสือ และอ่างแช่น้ำลึก"],
  ["Our largest suite, with a private balcony facing the water.", "水辺に面した専用バルコニーを備えた、当ホテル最大のスイートです。", "我们最大的套房，设有面向海面的私人阳台。", "ห้องสวีทขนาดใหญ่ที่สุดของเรา พร้อมระเบียงส่วนตัวหันหน้าออกสู่ทะเล"],
  ["View Details", "詳細を見る", "查看详情", "ดูรายละเอียด"],
  ["/ night", "／泊", "／晚", "／คืน"],
  ["Guest Reviews", "お客様の声", "住客评价", "รีวิวจากผู้เข้าพัก"],
  ["What Our Guests Say", "お客様の声", "住客怎么说", "ผู้เข้าพักพูดถึงเราอย่างไร"],
  ["The quietest, cleanest hotel I've stayed at in years. Exactly what I needed.", "ここ数年で泊まった中で最も静かで清潔なホテルです。まさに求めていた場所でした。", "这是我多年来住过最安静、最干净的酒店，正是我需要的地方。", "โรงแรมที่เงียบและสะอาดที่สุดที่เคยพักมาหลายปี ตรงกับสิ่งที่ต้องการพอดี"],
  ["Simple, honest, and comfortable. The staff went out of their way to help.", "シンプルで誠実、そして快適です。スタッフは親身になって助けてくれました。", "简单、真诚又舒适，工作人员非常热心地提供帮助。", "เรียบง่าย จริงใจ และสบาย พนักงานดูแลช่วยเหลืออย่างเต็มที่"],
  ["Loved the ocean suite. Would happily come back every summer.", "オーシャンスイートが気に入りました。毎年夏に戻ってきたいです。", "非常喜欢海景套房，每年夏天都愿意再来。", "ชอบห้องสวีทวิวทะเลมาก ยินดีกลับมาทุกฤดูร้อน"],
  ["Ready for a quiet stay?", "静かな滞在の準備はできましたか？", "准备好享受宁静的住宿了吗？", "พร้อมสำหรับการพักผ่อนอย่างสงบหรือยัง"],
  ["Rooms fill quickly during peak season — reserve yours today.", "繁忙期は客室が早く埋まります。今すぐご予約ください。", "旺季客房很快售罄，今天就预订吧。", "ห้องพักเต็มเร็วในช่วงฤดูท่องเที่ยว จองวันนี้เลย"],
  ["Book Your Room", "客室を予約する", "预订客房", "จองห้องพัก"],
  ["Stay Updated", "最新情報", "获取最新消息", "อัปเดตข่าวสาร"],
  ["Join Our Newsletter", "ニュースレターに登録", "订阅我们的新闻通讯", "สมัครรับจดหมายข่าว"],
  ["Get seasonal offers and updates delivered to your inbox.", "季節のお得な情報や最新ニュースをメールでお届けします。", "将季节优惠和最新消息发送到您的邮箱。", "รับข้อเสนอประจำฤดูกาลและข่าวสารส่งตรงถึงอีเมล"],
  ["Your email address", "メールアドレス", "您的邮箱地址", "อีเมลของคุณ"],
  ["Subscribe", "登録する", "订阅", "สมัครรับข่าวสาร"],
  ["Explore", "サイトを見る", "探索", "สำรวจ"],
  ["Contact", "お問い合わせ", "联系我们", "ติดต่อเรา"],
  ["Hours", "営業時間", "营业时间", "เวลาทำการ"],
  ["Front Desk: 24/7", "フロントデスク：24時間年中無休", "前台：全天候服务", "แผนกต้อนรับ: 24 ชั่วโมง"],
  ["Check-in: 3:00 PM", "チェックイン：15:00", "入住：下午3:00", "เช็กอิน: 15:00 น."],
  ["Check-out: 11:00 AM", "チェックアウト：11:00", "退房：上午11:00", "เช็กเอาต์: 11:00 น."],
  ["Privacy Policy · Terms of Service", "プライバシーポリシー · 利用規約", "隐私政策 · 服务条款", "นโยบายความเป็นส่วนตัว · เงื่อนไขการให้บริการ"],
  ["Accommodations", "宿泊施設", "住宿", "ที่พัก"],
  ["Every room is designed for rest, with quality linens, quiet AC, and honest pricing.", "すべての客室は休息のために設計されています。上質なリネン、静かな空調、明朗な料金をご用意しています。", "每间客房都为休息而设计，配备优质床品、安静空调和透明价格。", "ห้องพักทุกห้องออกแบบเพื่อการพักผ่อน พร้อมผ้าปูคุณภาพ เครื่องปรับอากาศเงียบ และราคาที่จริงใจ"],
  ["A calm, well-lit room with a queen bed, work desk, and rain shower. Ideal for solo travelers or couples on a short stay.", "クイーンベッド、ワークデスク、レインシャワーを備えた明るく穏やかな客室。ひとり旅や短期のカップル旅行に最適です。", "宁静明亮的客房，配有大床、工作桌和雨淋花洒，适合独自旅行者或短住情侣。", "ห้องพักสงบสว่าง พร้อมเตียงควีน โต๊ะทำงาน และฝักบัวเรนชาวเวอร์ เหมาะสำหรับผู้เดินทางคนเดียวหรือคู่รักที่พักระยะสั้น"],
  ["More space, a reading corner, and a deep soaking tub. Perfect for guests staying longer and wanting extra comfort.", "ゆとりの空間、読書コーナー、深めのバスタブ。長期滞在やさらなる快適さを求めるお客様に最適です。", "更大的空间、阅读角和深泡浴缸，适合长期入住及追求额外舒适的客人。", "พื้นที่กว้างขึ้น มุมอ่านหนังสือ และอ่างแช่น้ำลึก เหมาะสำหรับผู้เข้าพักระยะยาวที่ต้องการความสบายยิ่งขึ้น"],
  ["Our largest suite, with a private balcony facing the water, a separate living area, and premium bath amenities.", "水辺に面した専用バルコニー、独立したリビング、上質なバスアメニティを備えた当ホテル最大のスイートです。", "我们最大的套房，设有面向海面的私人阳台、独立起居区和高级浴室用品。", "ห้องสวีทขนาดใหญ่ที่สุด พร้อมระเบียงส่วนตัวหันหน้าออกสู่ทะเล พื้นที่นั่งเล่นแยก และสิ่งอำนวยความสะดวกในห้องน้ำระดับพรีเมียม"],
  ["Queen bed", "クイーンベッド", "大床", "เตียงควีน"], ["King bed", "キングベッド", "特大床", "เตียงคิง"], ["King bed + sofa bed", "キングベッド＋ソファベッド", "特大床＋沙发床", "เตียงคิง + โซฟาเบด"],
  ["Free Wi-Fi", "無料Wi-Fi", "免费Wi-Fi", "Wi-Fi ฟรี"], ["Air conditioning", "エアコン", "空调", "เครื่องปรับอากาศ"], ["Rain shower", "レインシャワー", "雨淋花洒", "ฝักบัวเรนชาวเวอร์"], ["Mini fridge", "ミニ冷蔵庫", "迷你冰箱", "ตู้เย็นขนาดเล็ก"], ["Daily housekeeping", "毎日の清掃", "每日客房清洁", "ทำความสะอาดทุกวัน"],
  ["Soaking tub", "深めのバスタブ", "泡澡浴缸", "อ่างแช่น้ำ"], ["Reading nook", "読書コーナー", "阅读角", "มุมอ่านหนังสือ"], ["Mini bar", "ミニバー", "迷你吧", "มินิบาร์"], ["Turndown service", "ターンダウンサービス", "夜床服务", "บริการจัดเตียงช่วงค่ำ"],
  ["Private balcony", "専用バルコニー", "私人阳台", "ระเบียงส่วนตัว"], ["Living area", "リビングエリア", "起居区", "พื้นที่นั่งเล่น"], ["Espresso machine", "エスプレッソマシン", "浓缩咖啡机", "เครื่องชงเอสเปรสโซ"], ["Bathtub & rain shower", "バスタブ＆レインシャワー", "浴缸和雨淋花洒", "อ่างอาบน้ำและเรนชาวเวอร์"], ["Priority housekeeping", "優先清掃サービス", "优先客房清洁", "บริการทำความสะอาดแบบเร่งด่วน"],
  ["Reserve This Room", "この客室を予約", "预订此客房", "จองห้องนี้"], ["Policies", "ポリシー", "政策", "นโยบาย"], ["Good to Know", "知っておきたいこと", "须知", "ข้อมูลน่ารู้"], ["Check-in / Check-out", "チェックイン／チェックアウト", "入住／退房", "เช็กอิน / เช็กเอาต์"], ["Check-in from 3:00 PM, check-out by 11:00 AM. Early check-in on request.", "チェックインは15:00から、チェックアウトは11:00まで。アーリーチェックインは要相談です。", "下午3:00起入住，上午11:00前退房。可申请提前入住。", "เช็กอินตั้งแต่ 15:00 น. เช็กเอาต์ภายใน 11:00 น. ขอเช็กอินก่อนเวลาได้ตามคำขอ"],
  ["Free Cancellation", "無料キャンセル", "免费取消", "ยกเลิกฟรี"], ["Cancel up to 48 hours before arrival for a full refund.", "到着の48時間前までなら全額返金でキャンセルできます。", "抵达前48小时取消可获全额退款。", "ยกเลิกก่อนเดินทางมาถึง 48 ชั่วโมงเพื่อรับเงินคืนเต็มจำนวน"], ["Pet Friendly", "ペット同伴可", "宠物友好", "นำสัตว์เลี้ยงเข้าพักได้"], ["Small pets welcome in select rooms with advance notice.", "一部の客室では、事前連絡により小型ペットをお迎えできます。", "部分客房接受小型宠物入住，请提前告知。", "ยินดีต้อนรับสัตว์เลี้ยงขนาดเล็กในห้องที่กำหนดเมื่อแจ้งล่วงหน้า"], ["Found your room?", "お気に入りの客室は見つかりましたか？", "找到心仪的客房了吗？", "พบห้องที่ถูกใจแล้วหรือยัง"], ["Reach out and we'll help you finalize your reservation.", "お問い合わせいただければ、ご予約の確定をお手伝いします。", "联系我们，我们会协助您完成预订。", "ติดต่อเรา แล้วเราจะช่วยยืนยันการจองให้เรียบร้อย"], ["Contact Us", "お問い合わせ", "联系我们", "ติดต่อเรา"],
  ["On-Site Facilities", "館内施設", "酒店设施", "สิ่งอำนวยความสะดวกภายในโรงแรม"], ["Everything you need for a comfortable stay, all under one roof.", "快適な滞在に必要なものを、すべて館内に揃えています。", "舒适住宿所需的一切，尽在酒店之中。", "ทุกสิ่งที่จำเป็นสำหรับการเข้าพักแสนสบายรวมอยู่ในที่เดียว"], ["Facilities", "施設", "设施", "สิ่งอำนวยความสะดวก"], ["What's Included", "含まれるサービス", "包含项目", "สิ่งที่รวมอยู่"], ["Access to most amenities is complimentary for all guests.", "ほとんどの施設はすべてのお客様が無料でご利用いただけます。", "大多数设施均向所有住客免费开放。", "สิ่งอำนวยความสะดวกส่วนใหญ่ให้บริการฟรีสำหรับผู้เข้าพักทุกคน"],
  ["High-speed internet throughout the hotel and all guest rooms.", "ホテル全館とすべての客室で高速インターネットをご利用いただけます。", "全酒店及所有客房均提供高速网络。", "อินเทอร์เน็ตความเร็วสูงทั่วโรงแรมและห้องพักทุกห้อง"], ["Rooftop Pool", "屋上プール", "屋顶泳池", "สระว่ายน้ำบนดาดฟ้า"], ["Open daily from 7 AM to 9 PM with ocean views.", "毎日7:00から21:00まで、海を眺めながらご利用いただけます。", "每日早7点至晚9点开放，可欣赏海景。", "เปิดทุกวัน 7:00-21:00 น. พร้อมวิวทะเล"], ["Fitness Center", "フィットネスセンター", "健身中心", "ฟิตเนสเซ็นเตอร์"], ["24-hour access to modern equipment and free weights.", "最新の器具とフリーウェイトを24時間ご利用いただけます。", "全天候使用现代器械和自由重量设备。", "ใช้อุปกรณ์ทันสมัยและเวทอิสระได้ตลอด 24 ชั่วโมง"], ["Spa & Wellness", "スパ＆ウェルネス", "水疗与健康", "สปาและสุขภาพ"], ["Massage, sauna, and treatment rooms — bookable at the front desk.", "マッサージ、サウナ、施術室をご利用いただけます。フロントでご予約ください。", "提供按摩、桑拿和护理室服务，可在前台预订。", "บริการนวด ซาวน่า และห้องทรีตเมนต์ จองได้ที่แผนกต้อนรับ"], ["Restaurant & Bar", "レストラン＆バー", "餐厅与酒吧", "ร้านอาหารและบาร์"], ["Seasonal menu served for breakfast, lunch, and dinner.", "朝食、昼食、夕食に季節のメニューをご提供します。", "早餐、午餐和晚餐供应时令菜单。", "เสิร์ฟเมนูตามฤดูกาลสำหรับอาหารเช้า กลางวัน และเย็น"], ["Free Parking", "無料駐車場", "免费停车", "ที่จอดรถฟรี"], ["On-site parking available for all registered guests.", "ご登録のお客様は館内駐車場をご利用いただけます。", "所有登记住客均可使用酒店停车场。", "มีที่จอดรถภายในโรงแรมสำหรับผู้เข้าพักที่ลงทะเบียนทุกคน"], ["Airport Shuttle", "空港シャトル", "机场接送", "รถรับส่งสนามบิน"], ["Complimentary shuttle service, available on request.", "ご要望に応じて無料シャトルをご用意します。", "可按需提供免费接送服务。", "บริการรถรับส่งฟรีเมื่อแจ้งความประสงค์"], ["Laundry Service", "ランドリーサービス", "洗衣服务", "บริการซักรีด"], ["Same-day laundry and dry cleaning available.", "当日仕上げの洗濯・ドライクリーニングをご利用いただけます。", "提供当日洗衣和干洗服务。", "บริการซักรีดและซักแห้งเสร็จภายในวันเดียว"], ["Our team is available around the clock for any request.", "スタッフが24時間いつでもご要望に対応します。", "我们的团队全天候为您服务。", "ทีมงานพร้อมให้บริการทุกความต้องการตลอด 24 ชั่วโมง"],
  ["Gallery", "ギャラリー", "画廊", "แกลเลอรี"], ["Around the Hotel", "ホテルの風景", "酒店周边", "บรรยากาศรอบโรงแรม"], ["Extra Services", "追加サービス", "额外服务", "บริการเสริม"], ["Add to Your Stay", "滞在に追加", "为您的住宿增添服务", "เพิ่มบริการให้การเข้าพัก"], ["Optional services available for booking during your reservation.", "ご予約時に追加できるオプションサービスです。", "预订期间可选择的额外服务。", "บริการเสริมที่จองเพิ่มได้ระหว่างการจองที่พัก"], ["Airport Transfer", "空港送迎", "机场接送", "บริการรับส่งสนามบิน"], ["Private car pickup and drop-off, available 24/7.", "専用車による送迎を24時間ご利用いただけます。", "提供全天候私人车辆接送。", "บริการรถส่วนตัวรับส่งตลอด 24 ชั่วโมง"], ["/ one way", "／片道", "／单程", "／เที่ยวเดียว"], ["Spa Package", "スパパッケージ", "水疗套餐", "แพ็กเกจสปา"], ["60-minute massage plus sauna access for two.", "60分のマッサージと2名様分のサウナ利用。", "60分钟按摩及两人桑拿体验。", "นวด 60 นาทีพร้อมใช้บริการซาวน่าสำหรับสองท่าน"], ["/ package", "／パッケージ", "／套餐", "／แพ็กเกจ"], ["Breakfast Add-on", "朝食追加", "早餐加购", "เพิ่มอาหารเช้า"], ["Daily breakfast buffet for the full length of your stay.", "滞在期間中、毎日朝食ビュッフェをお楽しみいただけます。", "入住期间每日享用早餐自助餐。", "บุฟเฟต์อาหารเช้าทุกวันตลอดการเข้าพัก"], ["/ person / day", "／1名／1日", "／每人／每天", "／คน / วัน"], ["Curious about a service?", "サービスについて知りたいですか？", "想了解某项服务吗？", "สนใจบริการใดเป็นพิเศษหรือไม่"], ["Have questions about our amenities? Check our FAQ or reach out directly.", "施設についてご質問ですか？よくある質問をご覧いただくか、直接お問い合わせください。", "对我们的设施有疑问？请查看常见问题或直接联系我们。", "มีคำถามเกี่ยวกับสิ่งอำนวยความสะดวกหรือไม่ ดูคำถามที่พบบ่อยหรือติดต่อเราโดยตรง"], ["Read FAQ", "よくある質問を見る", "阅读常见问题", "อ่านคำถามที่พบบ่อย"],
  ["Get in Touch", "お問い合わせ", "联系我们", "ติดต่อเรา"], ["Contact & Reservations", "お問い合わせとご予約", "联系与预订", "ติดต่อและสำรองห้องพัก"], ["Questions, special requests, or ready to book? We're here to help.", "ご質問、特別なご要望、ご予約のご相談はお気軽にどうぞ。", "有疑问、特殊需求或准备预订？我们随时为您服务。", "มีคำถาม คำขอพิเศษ หรือพร้อมจองแล้วหรือยัง เราพร้อมช่วยเหลือ"], ["Reach Us", "お問い合わせ先", "联系我们", "ช่องทางติดต่อ"], ["Contact Information", "連絡先情報", "联系信息", "ข้อมูลการติดต่อ"], ["Our front desk team is available 24/7 for reservations and guest support.", "フロントデスクは24時間年中無休で、ご予約とお客様のサポートに対応します。", "前台全天候为您提供预订和住客支持。", "ทีมแผนกต้อนรับพร้อมให้บริการจองห้องพักและช่วยเหลือผู้เข้าพักตลอด 24 ชั่วโมง"], ["Address", "住所", "地址", "ที่อยู่"], ["Phone", "電話", "电话", "โทรศัพท์"], ["Email", "メール", "邮箱", "อีเมล"], ["Front Desk Hours", "フロント営業時間", "前台营业时间", "เวลาทำการแผนกต้อนรับ"], ["Open 24 hours, every day", "毎日24時間営業", "每天全天候开放", "เปิดบริการ 24 ชั่วโมงทุกวัน"], ["Map showing Heiwa Hotel location", "Heiwaホテルの場所を示す地図", "显示Heiwa酒店位置的地图", "แผนที่แสดงที่ตั้งโรงแรม Heiwa"], ["Send a Message", "メッセージを送る", "发送消息", "ส่งข้อความ"], ["Reservation Inquiry", "予約に関するお問い合わせ", "预订咨询", "สอบถามการจอง"], ["Share your dates, room preference, or special request and we’ll get back to you quickly.", "ご希望の日程、客室、特別なご要望をお知らせください。すぐにご返信します。", "请告诉我们您的日期、房型偏好或特殊需求，我们会尽快回复。", "แจ้งวันที่ ประเภทห้อง หรือคำขอพิเศษ แล้วเราจะติดต่อกลับโดยเร็ว"], ["Full Name", "氏名", "姓名", "ชื่อ-นามสกุล"], ["Your name", "お名前", "您的姓名", "ชื่อของคุณ"], ["New Reservation", "新規予約", "新预订", "การจองใหม่"], ["Existing Booking", "既存の予約", "已有预订", "การจองที่มีอยู่"], ["Group / Event", "団体／イベント", "团体／活动", "กลุ่ม / งานอีเวนต์"], ["General Question", "一般的な質問", "一般问题", "คำถามทั่วไป"], ["Message", "メッセージ", "留言", "ข้อความ"], ["Tell us about your stay or any special requests...", "滞在について、または特別なご要望をお聞かせください…", "请告诉我们您的住宿计划或特殊需求……", "แจ้งรายละเอียดการเข้าพักหรือคำขอพิเศษของคุณ..."], ["We typically respond within 24 hours.", "通常24時間以内に返信します。", "我们通常会在24小时内回复。", "โดยปกติเราจะตอบกลับภายใน 24 ชั่วโมง"], ["Send Message", "メッセージを送信", "发送留言", "ส่งข้อความ"], ["Quick Answers", "よくある質問", "快速解答", "คำตอบด่วน"], ["Before You Reach Out", "お問い合わせの前に", "联系我们之前", "ก่อนติดต่อเรา"], ["Many common questions are answered on our FAQ page.", "よくあるご質問は、よくある質問ページでご案内しています。", "许多常见问题已在常见问题页面解答。", "คำถามทั่วไปจำนวนมากมีคำตอบอยู่ในหน้าคำถามที่พบบ่อย"], ["Booking Help", "予約サポート", "预订帮助", "ช่วยเหลือการจอง"], ["Learn about availability, deposits, and confirmation emails.", "空室状況、デポジット、予約確認メールについてご案内します。", "了解房态、押金和确认邮件。", "เรียนรู้เกี่ยวกับห้องว่าง เงินมัดจำ และอีเมลยืนยัน"], ["Cancellations", "キャンセル", "取消预订", "การยกเลิก"], ["Review our 48-hour free cancellation policy.", "48時間前まで無料でキャンセルできるポリシーをご確認ください。", "查看我们提前48小时免费取消的政策。", "ดูนโยบายยกเลิกฟรีภายใน 48 ชั่วโมง"], ["Group Stays", "団体での滞在", "团体住宿", "การเข้าพักแบบกลุ่ม"], ["Ask about rates for weddings, retreats, and corporate stays.", "結婚式、リトリート、法人利用の料金についてお問い合わせください。", "咨询婚礼、休养旅行和商务住宿的价格。", "สอบถามราคาสำหรับงานแต่งงาน รีทรีต และการเข้าพักเพื่อธุรกิจ"], ["Visit FAQ Page", "よくある質問ページへ", "访问常见问题页面", "ไปหน้าคำถามที่พบบ่อย"],
  ["Help Center", "ヘルプセンター", "帮助中心", "ศูนย์ช่วยเหลือ"], ["Frequently Asked Questions", "よくある質問", "常见问题", "คำถามที่พบบ่อย"], ["Answers to the questions we hear most from our guests.", "お客様からよくいただくご質問への回答です。", "这里解答住客最常提出的问题。", "คำตอบสำหรับคำถามที่ผู้เข้าพักถามบ่อยที่สุด"], ["Search a question, e.g. 'cancellation'", "質問を検索（例：「キャンセル」）", "搜索问题，例如“取消”", "ค้นหาคำถาม เช่น 'การยกเลิก'"], ["All", "すべて", "全部", "ทั้งหมด"], ["Booking", "予約", "预订", "การจอง"], ["Policies", "ポリシー", "政策", "นโยบาย"], ["How do I book a room?", "客室はどのように予約できますか？", "如何预订客房？", "ฉันจะจองห้องพักได้อย่างไร"], ["Can I modify or cancel my reservation?", "予約の変更やキャンセルはできますか？", "可以修改或取消预订吗？", "ฉันสามารถเปลี่ยนแปลงหรือยกเลิกการจองได้หรือไม่"], ["Do you require a deposit at booking?", "予約時にデポジットは必要ですか？", "预订时需要押金吗？", "ต้องวางเงินมัดจำเมื่อจองหรือไม่"], ["What time is check-in and check-out?", "チェックインとチェックアウトの時間は？", "入住和退房时间是什么？", "เช็กอินและเช็กเอาต์กี่โมง"], ["Is parking available on-site?", "敷地内に駐車場はありますか？", "酒店提供停车位吗？", "มีที่จอดรถภายในโรงแรมหรือไม่"], ["Are pets allowed?", "ペットは同伴できますか？", "允许携带宠物吗？", "อนุญาตให้นำสัตว์เลี้ยงเข้าพักหรือไม่"], ["What is included in each room?", "各客室には何が含まれますか？", "每间客房包含哪些设施？", "ห้องพักแต่ละห้องมีอะไรบ้าง"], ["Do you offer connecting or family rooms?", "コネクティングルームやファミリールームはありますか？", "提供连通房或家庭房吗？", "มีห้องเชื่อมต่อหรือห้องสำหรับครอบครัวหรือไม่"], ["Is breakfast included in the room rate?", "宿泊料金に朝食は含まれますか？", "房价包含早餐吗？", "อาหารเช้ารวมอยู่ในราคาห้องหรือไม่"], ["Do you have a pool or gym?", "プールやジムはありますか？", "酒店有泳池或健身房吗？", "มีสระว่ายน้ำหรือฟิตเนสหรือไม่"], ["Is airport transportation available?", "空港送迎は利用できますか？", "提供机场接送吗？", "มีบริการรับส่งสนามบินหรือไม่"], ["What is your smoking policy?", "喫煙ポリシーは？", "酒店的吸烟政策是什么？", "นโยบายการสูบบุหรี่เป็นอย่างไร"], ["Still have questions?", "まだご質問がありますか？", "还有问题吗？", "ยังมีคำถามอยู่หรือไม่"], ["Our team is happy to help with anything not covered here.", "ここにないご質問にも、スタッフが喜んでお答えします。", "如有未涵盖的问题，我们的团队很乐意为您解答。", "ทีมงานยินดีช่วยตอบทุกเรื่องที่ไม่ได้กล่าวไว้ที่นี่"], ["No questions match your search. Try a different keyword or browse all categories.", "検索に一致する質問がありません。別のキーワードを試すか、すべてのカテゴリーをご覧ください。", "没有符合搜索条件的问题。请尝试其他关键词或浏览全部类别。", "ไม่พบคำถามที่ตรงกับการค้นหา ลองใช้คำค้นอื่นหรือดูทุกหมวดหมู่"],
  ["Check-out date must be after check-in date.", "チェックアウト日はチェックイン日より後にしてください。", "退房日期必须晚于入住日期。", "วันเช็กเอาต์ต้องหลังวันเช็กอิน"], ["Availability request received! We will confirm your reservation by email shortly.", "空室確認のリクエストを受け付けました。まもなくメールで予約を確認します。", "已收到空房查询请求！我们会很快通过邮件确认您的预订。", "ได้รับคำขอตรวจสอบห้องว่างแล้ว เราจะยืนยันการจองทางอีเมลในไม่ช้า"], ["Thank you for reaching out. Our team will respond within 24 hours.", "お問い合わせありがとうございます。24時間以内にスタッフから返信します。", "感谢您的联系。我们的团队将在24小时内回复。", "ขอบคุณที่ติดต่อเรา ทีมงานจะตอบกลับภายใน 24 ชั่วโมง"], ["You're subscribed! Watch your inbox for exclusive offers.", "登録が完了しました。限定オファーをメールでお届けします。", "订阅成功！请留意邮箱中的专属优惠。", "สมัครสำเร็จแล้ว รอติดตามข้อเสนอพิเศษในอีเมลของคุณ"]
];

translationRows.push(
  ["4 Guests", "4名", "4位客人", "4 คน"],
  ["\"The quietest, cleanest hotel I've stayed at in years. Exactly what I needed.\"", "「ここ数年で泊まった中で最も静かで清潔なホテルです。まさに求めていた場所でした。」", "“这是我多年来住过最安静、最干净的酒店，正是我需要的地方。”", "“โรงแรมที่เงียบและสะอาดที่สุดที่เคยพักมาหลายปี ตรงกับสิ่งที่ต้องการพอดี”"],
  ["\"Simple, honest, and comfortable. The staff went out of their way to help.\"", "「シンプルで誠実、そして快適です。スタッフは親身になって助けてくれました。」", "“简单、真诚又舒适，工作人员非常热心地提供帮助。”", "“เรียบง่าย จริงใจ และสบาย พนักงานดูแลช่วยเหลืออย่างเต็มที่”"],
  ["\"Loved the ocean suite. Would happily come back every summer.\"", "「オーシャンスイートが気に入りました。毎年夏に戻ってきたいです。」", "“非常喜欢海景套房，每年夏天都愿意再来。”", "“ชอบห้องสวีทวิวทะเลมาก ยินดีกลับมาทุกฤดูร้อน”"],
  ["© 2026 Heiwa Hotel. All rights reserved.", "© 2026 Heiwaホテル。無断転載を禁じます。", "© 2026 Heiwa酒店。保留所有权利。", "© 2026 Heiwa Hotel สงวนลิขสิทธิ์"],
  ["Use the booking widget on our home or rooms page to check availability, or contact us directly by phone or email. You'll receive a confirmation email once your reservation is secured.", "ホームまたは客室ページの予約フォームで空室を確認するか、電話またはメールで直接お問い合わせください。予約が確定すると確認メールが届きます。", "使用首页或客房页面的预订工具查询空房，或通过电话或邮箱直接联系我们。预订确认后，您会收到确认邮件。", "ใช้แบบฟอร์มจองบนหน้าแรกหรือหน้าห้องพักเพื่อตรวจสอบห้องว่าง หรือติดต่อเราทางโทรศัพท์หรืออีเมลโดยตรง เมื่อการจองได้รับการยืนยัน คุณจะได้รับอีเมลยืนยัน"],
  ["Yes. Reservations can be modified or cancelled free of charge up to 48 hours before your check-in date. Changes within 48 hours may be subject to a one-night fee.", "はい。チェックイン日の48時間前までなら、無料で予約の変更やキャンセルができます。48時間以内の変更には1泊分の料金がかかる場合があります。", "可以。入住日期前48小时可免费修改或取消预订。48小时内的更改可能收取一晚房费。", "ได้ การจองสามารถเปลี่ยนแปลงหรือยกเลิกได้ฟรีก่อนวันเช็กอิน 48 ชั่วโมง การเปลี่ยนแปลงภายใน 48 ชั่วโมงอาจมีค่าธรรมเนียมหนึ่งคืน"],
  ["A valid credit card is required to hold your reservation, but you will not be charged until check-in unless you book a non-refundable rate.", "予約を確保するには有効なクレジットカードが必要ですが、返金不可の料金プランを除き、チェックインまで請求はありません。", "需要有效信用卡来担保预订，但除非预订不可退款房价，否则入住前不会扣款。", "ต้องใช้บัตรเครดิตที่ใช้งานได้เพื่อยืนยันการจอง แต่จะยังไม่เรียกเก็บเงินจนกว่าจะเช็กอิน เว้นแต่จองอัตราที่ไม่สามารถคืนเงินได้"],
  ["Check-in begins at 3:00 PM and check-out is by 11:00 AM. Early check-in and late check-out can be arranged based on availability.", "チェックインは15:00から、チェックアウトは11:00までです。アーリーチェックインとレイトチェックアウトは空室状況により手配できます。", "入住从下午3:00开始，退房时间为上午11:00前。可根据房态安排提前入住和延迟退房。", "เช็กอินได้ตั้งแต่ 15:00 น. และเช็กเอาต์ภายใน 11:00 น. สามารถจัดเช็กอินก่อนเวลาหรือเช็กเอาต์ล่าช้าได้ตามห้องว่าง"],
  ["Yes, we offer free on-site parking for all registered guests, available 24 hours a day.", "はい、ご登録のお客様には24時間無料の館内駐車場をご用意しています。", "有，我们为所有登记住客提供全天候免费停车。", "มี เรามีที่จอดรถฟรีภายในโรงแรมสำหรับผู้เข้าพักที่ลงทะเบียนทุกคนตลอด 24 ชั่วโมง"],
  ["Small pets are welcome in select rooms with advance notice. Please mention your pet when booking so we can prepare accordingly.", "一部の客室では、事前にお知らせいただければ小型ペットをお迎えできます。準備のため、ご予約時にペット同伴をお知らせください。", "部分客房接受小型宠物入住，请提前告知。预订时请说明您将携带宠物，以便我们做好准备。", "ยินดีต้อนรับสัตว์เลี้ยงขนาดเล็กในห้องที่กำหนดเมื่อแจ้งล่วงหน้า โปรดแจ้งเรื่องสัตว์เลี้ยงเมื่อจองเพื่อให้เราเตรียมการได้เหมาะสม"],
  ["All rooms include free Wi-Fi, air conditioning, a private bathroom, daily housekeeping, and a mini fridge. Deluxe rooms and suites include additional amenities such as bathtubs and reading nooks.", "すべての客室に無料Wi-Fi、エアコン、専用バスルーム、毎日の清掃、ミニ冷蔵庫を完備しています。デラックスルームとスイートには、バスタブや読書コーナーなどの追加設備があります。", "所有客房均配备免费Wi-Fi、空调、私人浴室、每日清洁和迷你冰箱。豪华客房和套房还配有浴缸和阅读角等额外设施。", "ห้องพักทุกห้องมี Wi-Fi ฟรี เครื่องปรับอากาศ ห้องน้ำส่วนตัว บริการทำความสะอาดทุกวัน และตู้เย็นขนาดเล็ก ห้องดีลักซ์และห้องสวีทมีสิ่งอำนวยความสะดวกเพิ่มเติม เช่น อ่างอาบน้ำและมุมอ่านหนังสือ"],
  ["Yes, our Ocean Suites can accommodate up to four guests, and connecting rooms are available on request for families or groups.", "はい、オーシャンスイートは最大4名様までご利用いただけます。ご家族やグループ向けに、リクエストに応じてコネクティングルームもご用意します。", "有，我们的海景套房最多可容纳四位客人，家庭或团体可申请连通房。", "ได้ ห้องสวีทวิวทะเลรองรับผู้เข้าพักได้สูงสุดสี่คน และมีห้องเชื่อมต่อสำหรับครอบครัวหรือกลุ่มเมื่อร้องขอ"],
  ["Breakfast is not included by default but can be added to any reservation for $15 per person per day.", "朝食は通常含まれていませんが、1名1日15ドルでどのご予約にも追加できます。", "早餐默认不包含，但可按每人每天15美元添加到任何预订中。", "อาหารเช้าไม่รวมในราคามาตรฐาน แต่เพิ่มในการจองใดก็ได้ในราคา 15 ดอลลาร์ต่อคนต่อวัน"],
  ["Yes, guests have complimentary access to our rooftop pool (7 AM–9 PM) and 24-hour fitness center.", "はい。お客様は屋上プール（7:00〜21:00）と24時間営業のフィットネスセンターを無料でご利用いただけます。", "有，住客可免费使用屋顶泳池（早7点至晚9点）和全天候健身中心。", "มี ผู้เข้าพักใช้สระว่ายน้ำบนดาดฟ้า (7:00-21:00 น.) และฟิตเนส 24 ชั่วโมงได้ฟรี"],
  ["We offer an airport shuttle on request, as well as private transfers for $35 each way.", "ご要望に応じて空港シャトルをご用意します。専用送迎は片道35ドルです。", "我们可按需提供机场接送，也提供每程35美元的私人接送。", "เรามีรถรับส่งสนามบินเมื่อแจ้งความประสงค์ และบริการรับส่งส่วนตัวราคา 35 ดอลลาร์ต่อเที่ยว"],
  ["Heiwa Hotel is a fully non-smoking property. Smoking is permitted only in designated outdoor areas.", "Heiwaホテルは全館禁煙です。喫煙は指定された屋外エリアのみで可能です。", "Heiwa酒店全面禁烟，仅可在指定室外区域吸烟。", "Heiwa Hotel เป็นโรงแรมปลอดบุหรี่ทั้งหมด อนุญาตให้สูบบุหรี่เฉพาะพื้นที่กลางแจ้งที่กำหนด"]
);

const translations = Object.fromEntries(["en", "ja", "zh", "th"].map((language, index) => [
  language,
  Object.fromEntries(translationRows.map(([english, japanese, chinese, thai]) => [english, [english, japanese, chinese, thai][index]]))
]));

function translateValue(value, language) {
  return translations[language][value.trim()] || value;
}

function translatePage(language) {
  document.documentElement.lang = language;
  const dictionary = translations[language];
  const textWalker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let textNode;

  while ((textNode = textWalker.nextNode())) {
    if (textNode.parentElement.closest(".language-select, script")) continue;
    if (!textNode.originalHeiwaText) textNode.originalHeiwaText = textNode.nodeValue;
    const value = textNode.originalHeiwaText;
    const trimmed = value.trim();
    if (!trimmed) continue;
    const translated = dictionary[trimmed];
    if (translated) {
      textNode.nodeValue = value.replace(trimmed, translated);
    }
  }

  document.querySelectorAll("[placeholder], [aria-label], title, meta[name='description']").forEach((element) => {
    const attribute = element.tagName === "META" ? "content" : element.tagName === "TITLE" ? "textContent" : element.hasAttribute("placeholder") ? "placeholder" : "aria-label";
    const value = attribute === "textContent" ? element.textContent : attribute === "content" ? element.getAttribute(attribute) : element.getAttribute(attribute);
    if (!element.originalHeiwaValue) element.originalHeiwaValue = value;
    const translated = dictionary[element.originalHeiwaValue.trim()];
    if (!translated) return;
    if (attribute === "textContent") element.textContent = translated;
    else element.setAttribute(attribute, translated);
  });

  customSelectRefreshers.forEach((refresh) => refresh());
}

languageSelects.forEach((select) => {
  select.value = savedLanguage;
  select.addEventListener("change", () => {
    localStorage.setItem("heiwa-language", select.value);
    languageSelects.forEach((otherSelect) => {
      otherSelect.value = select.value;
    });
    translatePage(select.value);
  });
});

translatePage(savedLanguage);

// ===== Mobile nav toggle =====
const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });
}

// ===== Flatpickr date-range pickers for check-in / check-out =====
document.querySelectorAll(".date-range-input").forEach((input) => {
  const field = input.closest(".field-daterange");
  const checkIn = field.querySelector('input[name="check-in"]');
  const checkOut = field.querySelector('input[name="check-out"]');

  flatpickr(input, {
    mode: "range",
    dateFormat: "Y-m-d",
    altInput: true,
    altFormat: "M j, Y",
    minDate: "today",
    onOpen: () => document.body.classList.add("datepicker-open"),
    onClose: () => document.body.classList.remove("datepicker-open"),
    onChange: (selectedDates) => {
      checkIn.value = selectedDates[0] ? flatpickr.formatDate(selectedDates[0], "Y-m-d") : "";
      checkOut.value = selectedDates[1] ? flatpickr.formatDate(selectedDates[1], "Y-m-d") : "";
    },
  });
});

// ===== Booking form(s) =====
document.querySelectorAll(".booking-form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const checkIn = form.querySelector('[name="check-in"]');
    const checkOut = form.querySelector('[name="check-out"]');
    const message = form.querySelector(".form-message");

    if (checkIn && checkOut && checkOut.value && checkIn.value && checkOut.value <= checkIn.value) {
      showMessage(message, "Check-out date must be after check-in date.", "error");
      return;
    }

    showMessage(message, "Availability request received! We will confirm your reservation by email shortly.", "success");
    form.reset();
  });
});

// ===== Contact form =====
const contactForm = document.querySelector(".contact-form");
if (contactForm) {
  contactForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = contactForm.querySelector(".form-message");
    showMessage(message, "Thank you for reaching out. Our team will respond within 24 hours.", "success");
    contactForm.reset();
  });
}

// ===== Newsletter form =====
const newsletterForm = document.querySelector(".newsletter-form");
if (newsletterForm) {
  newsletterForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = newsletterForm.parentElement.querySelector(".form-message");
    showMessage(message, "You're subscribed! Watch your inbox for exclusive offers.", "success");
    newsletterForm.reset();
  });
}

function showMessage(el, text, type) {
  if (!el) return;
  el.textContent = text;
  el.classList.remove("success", "error");
  el.classList.add("show", type);
}

// ===== FAQ accordion =====
document.querySelectorAll(".faq-item").forEach((item) => {
  const question = item.querySelector(".faq-question");
  const answer = item.querySelector(".faq-answer");

  question.addEventListener("click", () => {
    const isOpen = item.classList.contains("open");

    document.querySelectorAll(".faq-item.open").forEach((openItem) => {
      if (openItem !== item) {
        openItem.classList.remove("open");
        openItem.querySelector(".faq-answer").style.maxHeight = null;
      }
    });

    item.classList.toggle("open", !isOpen);
    answer.style.maxHeight = !isOpen ? answer.scrollHeight + "px" : null;
  });
});

// ===== FAQ category filter =====
const faqFilters = document.querySelectorAll(".faq-filter");
const faqItems = document.querySelectorAll(".faq-item");
const faqEmpty = document.querySelector(".faq-empty");

faqFilters.forEach((filter) => {
  filter.addEventListener("click", () => {
    faqFilters.forEach((f) => f.classList.remove("active"));
    filter.classList.add("active");
    const category = filter.dataset.category;
    let visibleCount = 0;

    faqItems.forEach((item) => {
      const match = category === "all" || item.dataset.category === category;
      item.style.display = match ? "block" : "none";
      if (match) visibleCount++;
    });

    if (faqEmpty) faqEmpty.style.display = visibleCount === 0 ? "block" : "none";
  });
});

// ===== FAQ search =====
const faqSearch = document.querySelector("#faq-search");
if (faqSearch) {
  faqSearch.addEventListener("input", () => {
    const term = faqSearch.value.trim().toLowerCase();
    let visibleCount = 0;

    // reset category filter to "all" while searching
    faqFilters.forEach((f) => f.classList.remove("active"));
    const allFilter = document.querySelector('.faq-filter[data-category="all"]');
    if (allFilter) allFilter.classList.add("active");

    faqItems.forEach((item) => {
      const text = item.textContent.toLowerCase();
      const match = text.includes(term);
      item.style.display = match ? "block" : "none";
      if (match) visibleCount++;
    });

    if (faqEmpty) faqEmpty.style.display = visibleCount === 0 ? "block" : "none";
  });
}

// ===== Build a custom dropdown UI around a native <select>, keeping the =====
// ===== native element for its value/change-event/form semantics. =====
function enhanceSelect(nativeSelect) {
  if (nativeSelect.dataset.customSelectReady) return;
  nativeSelect.dataset.customSelectReady = "true";

  const wrapper = document.createElement("div");
  wrapper.className = "custom-select";

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "custom-select-trigger";
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");

  const triggerLabel = document.createElement("span");
  const arrow = document.createElement("span");
  arrow.className = "custom-select-arrow";
  arrow.setAttribute("aria-hidden", "true");
  trigger.append(triggerLabel, arrow);

  const list = document.createElement("ul");
  list.className = "custom-select-list";
  list.setAttribute("role", "listbox");

  nativeSelect.classList.add("custom-select-native");
  nativeSelect.setAttribute("tabindex", "-1");
  nativeSelect.setAttribute("aria-hidden", "true");

  if (nativeSelect.id) {
    trigger.id = `${nativeSelect.id}-trigger`;
    const associatedLabel = document.querySelector(`label[for="${nativeSelect.id}"]`);
    if (associatedLabel) associatedLabel.setAttribute("for", trigger.id);
  }

  nativeSelect.parentNode.insertBefore(wrapper, nativeSelect);
  wrapper.append(trigger, list, nativeSelect);

  let activeIndex = nativeSelect.selectedIndex;

  function render() {
    list.innerHTML = "";
    activeIndex = nativeSelect.selectedIndex;
    Array.from(nativeSelect.options).forEach((option, index) => {
      const li = document.createElement("li");
      li.className = "custom-select-option";
      li.setAttribute("role", "option");
      li.textContent = option.textContent;
      const isSelected = index === nativeSelect.selectedIndex;
      li.classList.toggle("selected", isSelected);
      li.setAttribute("aria-selected", String(isSelected));
      li.addEventListener("click", () => choose(index));
      list.appendChild(li);
    });
    triggerLabel.textContent = nativeSelect.options[nativeSelect.selectedIndex]?.textContent || "";
  }

  function choose(index) {
    if (nativeSelect.selectedIndex !== index) {
      nativeSelect.selectedIndex = index;
      nativeSelect.dispatchEvent(new Event("change", { bubbles: true }));
    }
    render();
    close();
    trigger.focus();
  }

  function open() {
    wrapper.classList.add("open");
    trigger.setAttribute("aria-expanded", "true");
    highlight(nativeSelect.selectedIndex);
    document.addEventListener("click", handleOutsideClick);
  }

  function close() {
    wrapper.classList.remove("open");
    trigger.setAttribute("aria-expanded", "false");
    document.removeEventListener("click", handleOutsideClick);
  }

  function handleOutsideClick(event) {
    if (!wrapper.contains(event.target)) close();
  }

  function highlight(index) {
    activeIndex = index;
    Array.from(list.children).forEach((li, i) => li.classList.toggle("active", i === index));
    list.children[index]?.scrollIntoView({ block: "nearest" });
  }

  trigger.addEventListener("click", () => {
    if (wrapper.classList.contains("open")) close();
    else open();
  });

  trigger.addEventListener("keydown", (event) => {
    const isOpen = wrapper.classList.contains("open");
    if (["ArrowDown", "ArrowUp", "Enter", " ", "Escape"].includes(event.key)) event.preventDefault();

    if (!isOpen) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) open();
      return;
    }

    if (event.key === "ArrowDown") highlight(Math.min(activeIndex + 1, nativeSelect.options.length - 1));
    else if (event.key === "ArrowUp") highlight(Math.max(activeIndex - 1, 0));
    else if (event.key === "Enter" || event.key === " ") choose(activeIndex);
    else if (event.key === "Escape") close();
  });

  render();
  customSelectRefreshers.push(render);
}

document.querySelectorAll("select").forEach(enhanceSelect);

// ===== Homepage banner spotlight =====
(function bannerSpotlight() {
  const hero = document.querySelector(".home-page .hero");
  if (!hero || window.matchMedia("(hover: none), (pointer: coarse)").matches) return;

  hero.addEventListener("mousemove", (event) => {
    const bounds = hero.getBoundingClientRect();
    hero.style.setProperty("--spotlight-x", `${event.clientX - bounds.left}px`);
    hero.style.setProperty("--spotlight-y", `${event.clientY - bounds.top}px`);
  });

  hero.addEventListener("mouseleave", () => {
    hero.style.removeProperty("--spotlight-x");
    hero.style.removeProperty("--spotlight-y");
  });
})();

// ===== Cursor follower circle =====
(function cursorFollower() {
  if (window.matchMedia("(hover: none), (pointer: coarse)").matches) return;

  const circle = document.createElement("div");
  circle.className = "cursor-circle";
  document.body.append(circle);

  let mouseX = 0;
  let mouseY = 0;
  let circleX = 0;
  let circleY = 0;
  let started = false;

  window.addEventListener("mousemove", (event) => {
    mouseX = event.clientX;
    mouseY = event.clientY;

    if (!started) {
      started = true;
      circleX = mouseX;
      circleY = mouseY;
      document.body.classList.add("cursor-ready");
    }
  });

  // circle eases toward the cursor for a fast, fluid trailing effect
  function animate() {
    circleX += (mouseX - circleX) * 0.35;
    circleY += (mouseY - circleY) * 0.35;
    circle.style.left = `${circleX}px`;
    circle.style.top = `${circleY}px`;
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);

  const hoverTargets = "a, button, input, select, textarea, .btn, [role='button']";
  document.addEventListener("mouseover", (event) => {
    if (event.target.closest(hoverTargets)) circle.classList.add("is-hover");
  });
  document.addEventListener("mouseout", (event) => {
    if (event.target.closest(hoverTargets)) circle.classList.remove("is-hover");
  });
})();
