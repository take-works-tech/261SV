import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SOLVIA — UIモックアップ一覧',
  description: '仕様に定義された画面と状態を事前確認するUIモックアップ。',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ja"><body>{children}</body></html>
}
