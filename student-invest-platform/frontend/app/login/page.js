"use client";

import { useState } from "react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();

    const res = await fetch(`${API_BASE_URL}/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (res.ok) {
      localStorage.setItem("access_token", data.access_token);
      setMessage("로그인 성공");
    } else {
      setMessage(data.detail || "로그인 실패");
    }
  }

  return (
    <div>
      <h1>로그인</h1>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "8px" }}>
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: "280px", padding: "8px" }}
          />
        </div>

        <div style={{ marginBottom: "8px" }}>
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "280px", padding: "8px" }}
          />
        </div>

        <button type="submit" style={{ padding: "8px 16px" }}>
          로그인
        </button>
      </form>

      <p>{message}</p>
    </div>
  );
}
