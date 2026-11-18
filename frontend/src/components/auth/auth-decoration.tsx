/** Decorative brand artwork; contains no product photos or live promotions. */
export function AuthDecoration({ side, login = false }: { side: "left" | "right"; login?: boolean }) {
  const bag = side === "left";
  const prefix = `auth-${side}`;
  return (
    <aside
      className={`auth-decoration auth-decoration-${side}`}
      aria-hidden="true"
    >
      {login && bag && <div className="login-bag-slogan">Siêu nhanh <span>– Siêu rẻ</span></div>}
      <svg viewBox="0 0 340 430" fill="none">
        <defs>
          <linearGradient
            id={`${prefix}-bag`}
            x1="90"
            y1="150"
            x2="285"
            y2="365"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#d0f1ff" />
            <stop offset=".4" stopColor="#88d3fc" />
            <stop offset="1" stopColor="#2098e3" />
          </linearGradient>
          <linearGradient
            id={`${prefix}-white`}
            x1="100"
            y1="250"
            x2="230"
            y2="405"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#fff" />
            <stop offset=".6" stopColor="#e1efff" />
            <stop offset="1" stopColor="#8dc6f2" />
          </linearGradient>
          <linearGradient
            id={`${prefix}-ribbon`}
            x1="140"
            y1="270"
            x2="220"
            y2="405"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#c9efff" />
            <stop offset=".4" stopColor="#279deb" />
            <stop offset="1" stopColor="#086ec7" />
          </linearGradient>
          <linearGradient id={`${prefix}-gold`} x1="0" y1="0" x2="1" y2="1">
            <stop stopColor="#fff9be" />
            <stop offset="1" stopColor="#ffc62c" />
          </linearGradient>
        </defs>
        <ellipse cx="173" cy="402" rx="153" ry="25" fill="#e2f5ff" />
        <ellipse
          cx="182"
          cy="393"
          rx="108"
          ry="15"
          fill="#4aa8df"
          opacity=".18"
        />
        {bag ? (
          <>
            <path
              d="M51 249C8 224 9 173 7 158c42 16 59 49 44 91ZM57 280c-41-3-54-33-57-48 39-3 61 19 57 48Z"
              fill="#81be51"
            />
            <path
              d="M274 343c45-40 55-51 58-78-42 2-66 33-58 78Z"
              fill="#95cb5d"
            />
            <path
              d="m77 161 174-9 29 222-229 7 26-220Z"
              fill={`url(#${prefix}-bag)`}
              stroke="#d5f2ff"
              strokeWidth="2"
            />
            <path d="m251 152 24 17 24 204-19 1-29-222Z" fill="#279fe6" />
            <path
              d="M109 174v-65c0-93 108-93 108 0v58"
              stroke="#2a91d6"
              strokeWidth="15"
            />
            <path
              d="M105 173v-65c0-89 106-89 106 0v59"
              stroke="#aee6ff"
              strokeWidth="9"
            />
            <circle cx="105" cy="178" r="6" fill="#1582c5" />
            <circle cx="213" cy="174" r="6" fill="#1582c5" />
            <text
              x="95"
              y="285"
              fill="white"
              fontSize="53"
              fontWeight="850"
              fontStyle="italic"
              fontFamily="Arial, sans-serif"
            >
              coco
            </text>
          </>
        ) : (
          <>
            <path
              d="m78 102 166-32 22 106-166 32-22-106Z"
              fill={`url(#${prefix}-bag)`}
              stroke="#effaff"
              strokeWidth="4"
            />
            <path
              d="m220 75 20 104"
              stroke="#e6f6ff"
              strokeWidth="3"
              strokeDasharray="8 7"
            />
            <text
              x="123"
              y="168"
              fill="white"
              fontSize="74"
              fontWeight="800"
              fontFamily="Arial, sans-serif"
            >
              %
            </text>
            <ellipse
              cx="174"
              cy="160"
              rx="151"
              ry="40"
              transform="rotate(-20 174 160)"
              stroke="white"
              strokeWidth="5"
              opacity=".8"
            />
            <path
              d="m265 21-34 60h27l-11 43 51-68h-32l14-35h-15Z"
              fill={`url(#${prefix}-gold)`}
              stroke="#fff6ba"
              strokeWidth="2"
            />
          </>
        )}
        <g
          transform={
            bag ? "translate(0 0)" : "translate(0 -5) rotate(9 170 330)"
          }
        >
          <rect
            x="92"
            y="299"
            width="137"
            height="99"
            rx="10"
            fill={`url(#${prefix}-white)`}
          />
          <path d="m229 299 22-13v99l-22 13V299Z" fill="#90c6f2" />
          <path d="m92 299 24-17h135l-22 17H92Z" fill="#f5fcff" />
          <rect x="83" y="286" width="155" height="22" rx="6" fill="#f5fbff" />
          <path d="M154 286h22v112h-22V286Z" fill={`url(#${prefix}-ribbon)`} />
          <path
            d="M166 287c-69-2-62-53-31-32 19 13 31 32 31 32Zm0 0c59-1 67-51 33-32-17 9-33 32-33 32Z"
            fill={`url(#${prefix}-ribbon)`}
            stroke="#b6e5ff"
            strokeWidth="3"
          />
        </g>
        <path
          d="m45 65 5 14 15 5-15 6-5 16-6-16-14-6 14-5 6-14ZM297 237l5 13 13 5-13 4-5 14-5-14-13-4 13-5 5-13Z"
          fill={`url(#${prefix}-gold)`}
        />
        <path
          d="m271 34 8-16m5 25 16-12M59 125l-13-9"
          stroke="#269de8"
          strokeWidth="5"
          strokeLinecap="round"
        />
      </svg>
    </aside>
  );
}
