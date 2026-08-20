export const metadata = {
  title: "Student Invest Platform",
  description: "학생 대상 교육용 모의투자 플랫폼",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <header style={{ padding: "16px", borderBottom: "1px solid #ddd" }}>
          <strong>학생 모의투자 플랫폼</strong>
          <span style={{ marginLeft: "12px", fontSize: "12px", color: "#666" }}>
            교육용 모의투자 시뮬레이션이며 실제 매매 중개가 아닙니다.
          </span>
        </header>
        <main style={{ padding: "16px" }}>{children}</main>
      </body>
    </html>
  );
}
