const backendHostPort = process.env.BACKEND_HOSTPORT;

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    if (!backendHostPort) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `http://${backendHostPort}/:path*`,
      },
    ];
  },
};

export default nextConfig;
