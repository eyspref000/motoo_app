const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getUniverse() {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/universe/current`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return null;
    }

    return await res.json();
  } catch {
    return null;
  }
}

export default async function Home() {
  const universe = await getUniverse();

  return (
    <div>
      <h1>종목 유니버스</h1>
      <p>코스피 70 + 코스닥 30 기반 교육용 유니버스</p>

      {!universe || !universe.items || universe.items.length === 0 ? (
        <p>유니버스 데이터가 없습니다. 백엔드 시드를 실행하세요.</p>
      ) : (
        <table border="1" cellPadding="8">
          <thead>
            <tr>
              <th>시장</th>
              <th>종목코드</th>
              <th>종목명</th>
              <th>순위</th>
              <th>총점</th>
            </tr>
          </thead>
          <tbody>
            {universe.items.map((item) => (
              <tr key={`${item.market}-${item.stock_code}`}>
                <td>{item.market}</td>
                <td>{item.stock_code}</td>
                <td>{item.stock_name}</td>
                <td>{item.rank_no}</td>
                <td>{item.total_score ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p>
        <a href="/login">로그인</a>
      </p>
    </div>
  );
}
