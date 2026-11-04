import mysql from 'mysql2/promise';
import { MongoClient } from 'mongodb';

const g = globalThis;
export const pool = (g._pool ??= mysql.createPool({
  host: process.env.MYSQL_HOST,
  port: +process.env.MYSQL_PORT || 3306,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  waitForConnections: true,
  connectionLimit: 10,
  dateStrings: true,
}));

export async function mongo() {
  g._mongo ??= new MongoClient(process.env.MONGO_URI).connect();
  return (await g._mongo).db(process.env.MONGO_DB);
}
