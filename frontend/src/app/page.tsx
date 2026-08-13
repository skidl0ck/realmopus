import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex-1">
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-900 to-emerald-800 text-white">
        <div className="mx-auto max-w-6xl px-6 py-28">
          <p className="text-emerald-300 font-medium tracking-wide uppercase text-sm">
            Greenview Estates
          </p>
          <h1 className="mt-4 text-5xl font-serif font-medium leading-tight max-w-2xl">
            Own a lot today, pay at your own pace.
          </h1>
          <p className="mt-6 text-emerald-100 max-w-xl text-lg">
            Browse available lots, reserve online, and manage your installment
            payments — all in one place.
          </p>
          <div className="mt-10 flex gap-4">
            <Link
              href="/lots"
              className="rounded-full bg-white text-emerald-900 px-6 py-3 font-medium hover:bg-emerald-50 transition"
            >
              Browse available lots
            </Link>
            <Link
              href="/portal"
              className="rounded-full border border-white/40 px-6 py-3 font-medium hover:bg-white/10 transition"
            >
              Client portal login
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-20 grid gap-10 sm:grid-cols-3">
        {[
          {
            title: "Flexible payment terms",
            body: "Down payment plus fixed monthly installments, with transparent fees and penalty terms.",
          },
          {
            title: "Pay online, anytime",
            body: "Settle installments via PayPal or your preferred local e-wallet directly from your portal.",
          },
          {
            title: "Track everything",
            body: "See your balance, payment history, and receipts whenever you need them.",
          },
        ].map((f) => (
          <div key={f.title}>
            <h3 className="font-serif text-xl mb-2">{f.title}</h3>
            <p className="text-stone-600 text-sm leading-relaxed">{f.body}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
